# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from django.contrib.sites.models import Site
from django.db.models.signals import pre_delete

from djblets.siteconfig.models import SiteConfiguration

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import AuthBackendHook, SignalHook
from reviewboard.reviews.models import (ReviewRequest,
                                        ReviewRequestDraft)
from reviewboard.reviews.signals import (reply_publishing,
                                         review_publishing,
                                         review_request_closed,
                                         review_request_reopened)

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import (
    bugzilla_to_publish_errors,
)
from mozreview.errors import (
    ParentShipItError,
)
from mozreview.extra_data import (
    UNPUBLISHED_RRIDS_KEY,
    gen_child_rrs,
    gen_rrs_by_extra_data_key,
)
from mozreview.messages import (
    NEVER_USED_DESCRIPTION,
)
from mozreview.models import (
    get_bugzilla_api_key,
)
from mozreview.rb_utils import (
    get_obj_url,
)
from rbbz.auth import BugzillaBackend
from rbbz.diffs import build_plaintext_review
from rbbz.middleware import CorsHeaderMiddleware
from rbbz.resources import bugzilla_cookie_login_resource


AUTO_CLOSE_DESCRIPTION = """
Discarded automatically because parent review request was discarded.
"""

AUTO_SUBMITTED_DESCRIPTION = """
Submitted because the parent review request was submitted.
"""


class BugzillaExtension(Extension):
    middleware = [CorsHeaderMiddleware]

    resources = [
        bugzilla_cookie_login_resource,
    ]

    def initialize(self):
        AuthBackendHook(self, BugzillaBackend)

        # Any abortable signal hooks that talk to Bugzilla should have
        # sandbox_errors=False, since we don't want to complete the action if
        # updating Bugzilla failed for any reason.
        SignalHook(self, pre_delete, on_draft_pre_delete)
        SignalHook(self, review_publishing, on_review_publishing,
                   sandbox_errors=False)
        SignalHook(self, reply_publishing, on_reply_publishing,
                   sandbox_errors=False)
        SignalHook(self, review_request_closed,
                   on_review_request_closed_discarded)
        SignalHook(self, review_request_closed,
                   on_review_request_closed_submitted)
        SignalHook(self, review_request_reopened, on_review_request_reopened)


def get_reply_url(reply, site=None, siteconfig=None):
    """ Get the URL for a reply to a review.

    Since replies can have multiple comments, we can't link to a specific
    comment, so we link to the parent review which the reply is targeted at.
    """
    return get_obj_url(reply.base_reply_to, site=site, siteconfig=siteconfig)


def is_review_request_pushed(review_request):
    return str(review_request.extra_data.get('p2rb', False)) == "True"


def is_review_request_squashed(review_request):
    squashed = str(review_request.extra_data.get('p2rb.is_squashed', False))
    return squashed == "True"


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
    # based on other things attached to the model. This is a temporary fix until
    # we get more comprehensive draft deletion signals built into Review Board.
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

    if not is_review_request_squashed(review_request):
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
                                           UNPUBLISHED_RRIDS_KEY):
        child.close(ReviewRequest.DISCARDED,
                    user=user,
                    description=NEVER_USED_DESCRIPTION)

    review_request.extra_data['p2rb.discard_on_publish_rids'] = '[]'
    review_request.extra_data['p2rb.unpublished_rids'] = '[]'
    review_request.save()


@bugzilla_to_publish_errors
def on_review_publishing(user, review, **kwargs):
    """Comment in the bug and potentially r+ or clear a review flag.

    Note that a reviewer *must* have editbugs to set an attachment flag on
    someone else's attachment (i.e. the standard BMO review process).

    TODO: Report lack-of-editbugs properly; see bug 1119065.
    """
    review_request = review.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    site = Site.objects.get_current()
    siteconfig = SiteConfiguration.objects.get_current()
    comment = build_plaintext_review(review,
                                     get_obj_url(review, site,
                                                 siteconfig),
                                     {"user": user})
    b = Bugzilla(get_bugzilla_api_key(user))

    # TODO: Update all attachments in one call.  This is not possible right
    # now because we have to potentially mix changing and creating flags.

    if is_review_request_squashed(review_request):
        # Mirror the comment to the bug, unless it's a ship-it, in which
        # case throw an error.  Ship-its are allowed only on child commits.
        if review.ship_it:
            raise ParentShipItError

        [b.post_comment(int(bug_id), comment) for bug_id in
         review_request.get_bug_list()]
    else:
        diff_url = '%sdiff/#index_header' % get_obj_url(review_request)
        bug_id = int(review_request.get_bug_list()[0])

        if review.ship_it:
            commented = b.r_plus_attachment(bug_id, review.user.email,
                                            diff_url, comment)
        else:
            commented = b.cancel_review_request(bug_id, review.user.email,
                                                diff_url, comment)

        if comment and not commented:
            b.post_comment(bug_id, comment)


@bugzilla_to_publish_errors
def on_reply_publishing(user, reply, **kwargs):
    review_request = reply.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    b = Bugzilla(get_bugzilla_api_key(user))

    url = get_reply_url(reply)
    comment = build_plaintext_review(reply, url, {"user": user})
    b.post_comment(bug_id, comment)


def on_review_request_closed_discarded(user, review_request, type, **kwargs):
    if type != ReviewRequest.DISCARDED:
        return

    if is_review_request_squashed(review_request):
        # close_child_review_requests will call save on this review request, so
        # we don't have to worry about it.
        review_request.commit = None

        close_child_review_requests(user, review_request,
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
    if (not is_review_request_squashed(review_request) or
        type != ReviewRequest.SUBMITTED):
        return

    close_child_review_requests(user, review_request, ReviewRequest.SUBMITTED,
                                  AUTO_SUBMITTED_DESCRIPTION)


def close_child_review_requests(user, review_request, status,
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
                                           UNPUBLISHED_RRIDS_KEY):
        child.close(ReviewRequest.DISCARDED,
                    user=user,
                    description=NEVER_USED_DESCRIPTION)

    review_request.extra_data['p2rb.unpublished_rids'] = '[]'
    review_request.extra_data['p2rb.discard_on_publish_rids'] = '[]'
    review_request.save()


def on_review_request_reopened(user, review_request, **kwargs):
    if not is_review_request_squashed(review_request):
        return

    identifier = review_request.extra_data['p2rb.identifier']

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
            logging.error("Could not revive review request with ID %s "
                          "because its commit id (%s) is already being used by "
                          "a review request with ID %s."
                          % (review_request.id, identifier,
                             preexisting_review_request.id))
            # TODO: We need Review Board to recognize exceptions in these signal
            # handlers so that the UI can print out a useful message.
            raise Exception("Revive failed because a review request with commit ID %s "
                            "already exists." % identifier)
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
