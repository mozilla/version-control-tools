from __future__ import unicode_literals

import json
import logging

from django.db.models.signals import (
    post_save,
)

from djblets.siteconfig.models import (
    SiteConfiguration,
)
from reviewboard.extensions.hooks import (
    SignalHook,
)
from reviewboard.reviews.models import (
    ReviewRequest,
    ReviewRequestDraft,
)
from reviewboard.reviews.signals import (
    review_request_publishing,
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
    DRAFTED_EXTRA_DATA_KEYS,
    gen_child_rrs,
    gen_rrs_by_rids,
    get_parent_rr,
    is_parent,
    is_pushed,
    REVIEWID_RE,
    update_parent_rr_reviewers,
)
from mozreview.messages import (
    NEVER_USED_DESCRIPTION,
    OBSOLETE_DESCRIPTION,
)
from mozreview.models import (
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
        ensure_parent_draft,
        sender=ReviewRequestDraft)

    SignalHook(
        extension,
        review_request_publishing,
        on_review_request_publishing,
        sandbox_errors=False)


def ensure_parent_draft(sender, **kwargs):
    """Ensure parent draft exists when child has a draft.

    This is intended to handle the post_save signal for the
    ReviewRequestDraft model and ensure the parent review request
    has a draft if a child draft is saved. We need to do this so
    that the parent may always be published when a child requires
    publishing.

    Particularly we update our own reviewer information in the
    parent to make sure that a reviewer change on a child request
    will create a parent draft - even if the reviewer change does
    not alter the overall set of reviewers for the series.
    """
    instance = kwargs["instance"]
    rr = instance.get_review_request()

    if is_pushed(instance) and not is_parent(rr):
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
    reviewid = review_request_draft.extra_data.get('p2rb.identifier', None)
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
            review_request.extra_data['p2rb.unpublished_rids']))
        discard_on_publish_rids = map(int, json.loads(
            review_request.extra_data['p2rb.discard_on_publish_rids']))
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

        review_request.extra_data['p2rb.unpublished_rids'] = '[]'
        review_request.extra_data['p2rb.discard_on_publish_rids'] = '[]'

    # Copy p2rb extra data from the draft, overwriting the current
    # values on the review request.
    draft_extra_data = review_request_draft.extra_data

    for key in DRAFTED_EXTRA_DATA_KEYS:
        if key in draft_extra_data:
            review_request.extra_data[key] = draft_extra_data[key]

    review_request.save()
