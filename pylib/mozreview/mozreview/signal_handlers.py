from __future__ import unicode_literals

import copy
import json
import logging

from django.db.models.signals import (
    post_save,
    pre_delete,
)

from djblets.siteconfig.models import (
    SiteConfiguration,
)
from reviewboard.reviews.errors import (
    PublishError,
)
from reviewboard.extensions.hooks import (
    SignalHook,
)
from reviewboard.reviews.models import (
    ReviewRequest,
    ReviewRequestDraft,
)
from reviewboard.reviews.signals import (
    review_request_closed,
    review_request_publishing,
    review_request_reopened,
)

from mozreview.bugzilla.attachments import (
    post_bugzilla_attachment,
)
from mozreview.bugzilla.client import (
    Bugzilla,
)
from mozreview.bugzilla.errors import (
    BugzillaError,
    bugzilla_to_publish_errors,
)
from mozreview.errors import (
    CommitPublishProhibited,
    ConfidentialBugError,
    InvalidBugIdError,
)
from mozreview.extra_data import (
    DISCARD_ON_PUBLISH_KEY,
    DRAFTED_COMMIT_DATA_KEYS,
    DRAFTED_EXTRA_DATA_KEYS,
    gen_child_rrs,
    gen_rrs_by_extra_data_key,
    gen_rrs_by_rids,
    get_parent_rr,
    IDENTIFIER_KEY,
    is_parent,
    is_pushed,
    REVIEWID_RE,
    UNPUBLISHED_KEY,
    update_parent_rr_reviewers,
)
from mozreview.messages import (
    AUTO_CLOSE_DESCRIPTION,
    AUTO_SUBMITTED_DESCRIPTION,
    NEVER_USED_DESCRIPTION,
    OBSOLETE_DESCRIPTION,
)
from mozreview.models import (
    CommitData,
    DiffSetVerification,
    get_bugzilla_api_key,
)
from mozreview.rb_utils import (
    get_obj_url,
)
from mozreview.signals import (
    commit_request_publishing,
)


def initialize_signal_handlers(extension):
    """Initialize signal handlers.

    Any initialization of the signal handlers, including instantiating
    SignalHooks should take place inside this function. An extension
    should call it during initialize().

    Any abortable signal hooks that talk to Bugzilla should have
    sandbox_errors=False, since we don't want to complete the action if
    updating Bugzilla failed for any reason.
    """
    SignalHook(
        extension,
        post_save,
        post_save_review_request_draft,
        sender=ReviewRequestDraft)

    SignalHook(
        extension,
        pre_delete,
        on_draft_pre_delete)

    SignalHook(
        extension,
        review_request_reopened,
        on_review_request_reopened)

    SignalHook(
        extension,
        review_request_closed,
        on_review_request_closed_discarded)

    SignalHook(
        extension,
        review_request_closed,
        on_review_request_closed_submitted)

    SignalHook(
        extension,
        review_request_publishing,
        on_review_request_publishing,
        sandbox_errors=False)


def post_save_review_request_draft(sender, **kwargs):
    """Handle post_save for a ReviewRequestDraft."""
    draft = kwargs["instance"]

    if kwargs["created"] and not kwargs["raw"]:
        copy_commit_data(draft)

    ensure_parent_draft(draft)


def copy_commit_data(draft):
    """Copy CommitData for the draft.

    When a new draft is created we need to copy over extra_data
    to draft_extra_data inside the associated CommitData object.
    This makes our two extra_data fields mimic the built-in
    extra_data for ReviewRequest and ReviewRequestDraft.
    """
    commit_data = CommitData.objects.get_or_create(
        review_request_id=draft.review_request_id)[0]

    commit_data.draft_extra_data = copy.deepcopy(commit_data.extra_data)
    commit_data.save()


def ensure_parent_draft(draft):
    """Ensure parent draft exists when child has a draft.

    This is intended to be called in the post_save signal for the
    ReviewRequestDraft model and ensure the parent review request
    has a draft if a child draft is saved. We need to do this so
    that the parent may always be published when a child requires
    publishing.

    Particularly we update our own reviewer information in the
    parent to make sure that a reviewer change on a child request
    will create a parent draft - even if the reviewer change does
    not alter the overall set of reviewers for the series.
    """
    rr = draft.get_review_request()

    if is_pushed(draft) and not is_parent(rr):
        parent_rr = get_parent_rr(rr)
        parent_rr_draft = parent_rr.get_draft()

        if parent_rr_draft is None:
            parent_rr_draft = ReviewRequestDraft.create(parent_rr)

        update_parent_rr_reviewers(parent_rr_draft)


@bugzilla_to_publish_errors
def on_review_request_publishing(user, review_request_draft, **kwargs):
    # There have been strange cases (all local, and during development), where
    # when attempting to publish a review request, this handler will fail
    # because the draft does not exist. This is a really strange case, and not
    # one we expect to happen in production. However, since we've seen it
    # locally, we handle it here, and log.
    if not review_request_draft:
        logging.error('Strangely, there was no review request draft on the '
                      'review request we were attempting to publish.')
        return

    # If the review request draft has a new DiffSet we will only allow
    # publishing if that DiffSet has been verified. It is important to
    # do this for every review request, not just pushed ones, because
    # we can't trust the storage mechanism which indicates it was pushed.
    # TODO: This will be fixed when we transition away from extra_data.
    if review_request_draft.diffset:
        try:
            DiffSetVerification.objects.get(
                diffset=review_request_draft.diffset)
        except DiffSetVerification.DoesNotExist:
            logging.error(
                'An attempt was made by User %s to publish an unverified '
                'DiffSet with id %s',
                user.id,
                review_request_draft.diffset.id)

            raise PublishError(
                'This review request draft contained a manually uploaded '
                'diff, which is prohibited. Please push to the review server '
                'to create review requests. If you believe you received this '
                'message in error, please file a bug.')

    review_request = review_request_draft.get_review_request()

    # skip review requests that were not pushed
    if not is_pushed(review_request):
        return

    if not is_parent(review_request):
        # Send a signal asking for approval to publish this review request.
        # We only want to publish this commit request if we are in the middle
        # of publishing the parent. If the parent is publishing it will be
        # listening for this signal to approve it.
        approvals = commit_request_publishing.send_robust(
            sender=review_request,
            user=user,
            review_request_draft=review_request_draft)

        for receiver, approved in approvals:
            if approved:
                break
        else:
            # This publish is not approved by the parent review request.
            raise CommitPublishProhibited()

    # The reviewid passed through p2rb is, for Mozilla's instance anyway,
    # bz://<bug id>/<irc nick>.
    reviewid = review_request_draft.extra_data.get(IDENTIFIER_KEY, None)
    m = REVIEWID_RE.match(reviewid)

    if not m:
        raise InvalidBugIdError('<unknown>')

    bug_id = m.group(1)

    try:
        bug_id = int(bug_id)
    except (TypeError, ValueError):
        raise InvalidBugIdError(bug_id)

    siteconfig = SiteConfiguration.objects.get_current()
    using_bugzilla = (
        siteconfig.settings.get("auth_backend", "builtin") == "bugzilla")

    if using_bugzilla:
        b = Bugzilla(get_bugzilla_api_key(user))

        try:
            if b.is_bug_confidential(bug_id):
                raise ConfidentialBugError
        except BugzillaError as e:
            # Special cases:
            #   100: Invalid Bug Alias
            #   101: Bug does not exist
            if e.fault_code and (e.fault_code == 100 or e.fault_code == 101):
                raise InvalidBugIdError(bug_id)
            raise

    # Note that the bug ID has already been set when the review was created.

    # If this is a squashed/parent review request, automatically publish all
    # relevant children.
    if is_parent(review_request):
        unpublished_rids = map(int, json.loads(
            review_request.extra_data[UNPUBLISHED_KEY]))
        discard_on_publish_rids = map(int, json.loads(
            review_request.extra_data[DISCARD_ON_PUBLISH_KEY]))
        child_rrs = list(gen_child_rrs(review_request_draft))

        # Create or update Bugzilla attachments for each draft commit.  This
        # is done before the children are published to ensure that MozReview
        # doesn't get into a strange state if communication with Bugzilla is
        # broken or attachment creation otherwise fails.  The Bugzilla
        # attachments will then, of course, be in a weird state, but that
        # should be fixed by the next successful publish.
        if using_bugzilla:
            for child in child_rrs:
                child_draft = child.get_draft(user=user)

                if child_draft:
                    if child.id in discard_on_publish_rids:
                        b.obsolete_review_attachments(
                            bug_id, get_obj_url(child))
                    post_bugzilla_attachment(b, bug_id, child_draft, child)

        # Publish draft commits. This will already include items that are in
        # unpublished_rids, so we'll remove anything we publish out of
        # unpublished_rids.
        for child in child_rrs:
            if child.get_draft(user=user) or not child.public:
                def approve_publish(sender, user, review_request_draft,
                                    **kwargs):
                    return child is sender

                # Setup the parent signal handler to approve the publish
                # and then publish the child.
                commit_request_publishing.connect(approve_publish,
                                                  sender=child,
                                                  weak=False)
                try:
                    child.publish(user=user)
                finally:
                    commit_request_publishing.disconnect(
                        receiver=approve_publish,
                        sender=child,
                        weak=False)

                if child.id in unpublished_rids:
                    unpublished_rids.remove(child.id)

        # The remaining unpubished_rids need to be closed as discarded because
        # they have never been published, and they will appear in the user's
        # dashboard unless closed.
        for child in gen_rrs_by_rids(unpublished_rids):
            child.close(ReviewRequest.DISCARDED,
                        user=user,
                        description=NEVER_USED_DESCRIPTION)

        # We also close the discard_on_publish review requests because, well,
        # we don't need them anymore. We use a slightly different message
        # though.
        for child in gen_rrs_by_rids(discard_on_publish_rids):
            child.close(ReviewRequest.DISCARDED,
                        user=user,
                        description=OBSOLETE_DESCRIPTION)

        review_request.extra_data[UNPUBLISHED_KEY] = '[]'
        review_request.extra_data[DISCARD_ON_PUBLISH_KEY] = '[]'

    # Copy p2rb extra data from the draft, overwriting the current
    # values on the review request.
    draft_extra_data = review_request_draft.extra_data

    for key in DRAFTED_EXTRA_DATA_KEYS:
        if key in draft_extra_data:
            review_request.extra_data[key] = draft_extra_data[key]

    commit_data = CommitData.objects.get_or_create(
        review_request=review_request)[0]

    # Copy any drafted CommitData from draft_extra_data to extra_data.
    for key in DRAFTED_COMMIT_DATA_KEYS:
        if key in commit_data.draft_extra_data:
            commit_data.extra_data[key] = commit_data.draft_extra_data[key]

    commit_data.save(update_fields=['extra_data'])

    review_request.save()


def on_draft_pre_delete(sender, instance, using, **kwargs):
    """ Handle draft discards.

    There are no handy signals built into Review Board (yet) for us to detect
    when a squashed Review Request Draft is discarded. Instead, we monitor for
    deletions of models, and handle cases where the models being deleted are
    ReviewRequestDrafts. We then do some processing to ensure that the draft
    is indeed a draft of a squashed review request that we want to handle,
    and then propagate the discard down to the child review requests.
    """
    if not sender == ReviewRequestDraft:
        return

    # Drafts can get deleted for a number of reasons. They get deleted when
    # drafts are discarded, obviously, but also whenever review requests are
    # published, because the data gets copied over to the review request, and
    # then the draft is blown away. Unfortunately, on_pre_delete doesn't give
    # us too many clues about which scenario we're in, so we have to infer it
    # based on other things attached to the model. This is a temporary fix
    # until we get more comprehensive draft deletion signals built into Review
    # Board.
    #
    # In the case where the review request is NOT public yet, the draft will
    # not have a change description. In this case, we do not need to
    # differentiate between publish and discard because discards of non-public
    # review request's drafts will always cause the review request to be closed
    # as discarded, and this case is handled by on_review_request_closed().
    #
    # In the case where the review request has a change description, but it's
    # set to public, we must have just published this draft before deleting it,
    # so there's nothing to do here.
    if (instance.changedesc is None or instance.changedesc.public):
        return

    review_request = instance.review_request

    if not review_request:
        return

    if not is_parent(review_request):
        return

    # If the review request is marked as discarded, then we must be closing
    # it, and so the on_review_request_closed() handler will take care of it.
    if review_request.status == ReviewRequest.DISCARDED:
        return

    user = review_request.submitter

    for child in gen_child_rrs(review_request):
        draft = child.get_draft()
        if draft:
            draft.delete()

    for child in gen_rrs_by_extra_data_key(review_request,
                                           UNPUBLISHED_KEY):
        child.close(ReviewRequest.DISCARDED,
                    user=user,
                    description=NEVER_USED_DESCRIPTION)

    review_request.extra_data[DISCARD_ON_PUBLISH_KEY] = '[]'
    review_request.extra_data[UNPUBLISHED_KEY] = '[]'
    review_request.save()


def on_review_request_reopened(user, review_request, **kwargs):
    if not is_parent(review_request):
        return

    identifier = review_request.extra_data[IDENTIFIER_KEY]

    # If we're reviving a squashed review request that was discarded, it means
    # we're going to want to restore the commit ID field back, since we remove
    # it on discarding. This might be a problem if there's already a review
    # request with the same commit ID somewhere on Review Board, since commit
    # IDs are unique.
    #
    # When this signal fires, the state of the review request has already
    # changed, so we query for a review request with the same commit ID that is
    # not equal to the revived review request.
    try:
        preexisting_review_request = ReviewRequest.objects.get(
            commit_id=identifier, repository=review_request.repository)
        if preexisting_review_request != review_request:
            logging.error(
                'Could not revive review request with ID %s because its '
                'commit id (%s) is already being used by a review request '
                'with ID %s.' % (
                    review_request.id,
                    identifier,
                    preexisting_review_request.id))
            # TODO: We need Review Board to recognize exceptions in these
            # signal handlers so that the UI can print out a useful message.
            raise Exception(
                'Revive failed because a review request with commit ID %s '
                'already exists.' % identifier)
    except ReviewRequest.DoesNotExist:
        # Great! This is a success case.
        pass

    for child in gen_child_rrs(review_request):
        child.reopen(user=user)

    # If the review request had been discarded, then the commit ID would
    # have been cleared out. If the review request had been submitted,
    # this is a no-op, since the commit ID would have been there already.
    review_request.commit = identifier
    review_request.save()

    # If the review request has a draft, we have to set the commit ID there as
    # well, otherwise it'll get overwritten on publish.
    draft = review_request.get_draft(user)
    if draft:
        draft.commit = identifier
        draft.save()


def on_review_request_closed_discarded(user, review_request, type, **kwargs):
    if type != ReviewRequest.DISCARDED:
        return

    if is_parent(review_request):
        # close_child_review_requests will call save on this review request, so
        # we don't have to worry about it.
        review_request.commit = None

        _close_child_review_requests(user, review_request,
                                     ReviewRequest.DISCARDED,
                                     AUTO_CLOSE_DESCRIPTION)
    else:
        # TODO: Remove this once we properly prevent users from closing
        # commit review requests.
        b = Bugzilla(get_bugzilla_api_key(user))
        bug = int(review_request.get_bug_list()[0])
        diff_url = '%sdiff/#index_header' % get_obj_url(review_request)
        b.obsolete_review_attachments(bug, diff_url)


def on_review_request_closed_submitted(user, review_request, type, **kwargs):
    if (not is_parent(review_request) or
            type != ReviewRequest.SUBMITTED):
        return

    _close_child_review_requests(user, review_request, ReviewRequest.SUBMITTED,
                                 AUTO_SUBMITTED_DESCRIPTION)


def _close_child_review_requests(user, review_request, status,
                                 child_close_description):
    """Closes all child review requests for a squashed review request."""
    # At the point of closing, it's possible that if this review
    # request was never published, that most of the fields are empty
    # (See https://code.google.com/p/reviewboard/issues/detail?id=3465).
    # Luckily, the extra_data is still around, and more luckily, it's
    # not exposed in the UI for user-meddling. We can find all of the
    # child review requests via extra_data.p2rb.commits.
    for child in gen_child_rrs(review_request):
        child.close(status,
                    user=user,
                    description=child_close_description)

    # We want to discard any review requests that this squashed review
    # request never got to publish, so were never part of its "commits"
    # list.
    for child in gen_rrs_by_extra_data_key(review_request,
                                           UNPUBLISHED_KEY):
        child.close(ReviewRequest.DISCARDED,
                    user=user,
                    description=NEVER_USED_DESCRIPTION)

    review_request.extra_data[UNPUBLISHED_KEY] = '[]'
    review_request.extra_data[DISCARD_ON_PUBLISH_KEY] = '[]'
    review_request.save()
