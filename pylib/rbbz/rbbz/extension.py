# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import re

from django.contrib.sites.models import Site
from django.db.models.signals import pre_delete

from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import AuthBackendHook, SignalHook
from reviewboard.reviews.errors import PermissionError, PublishError
from reviewboard.reviews.models import (ReviewRequest,
                                        ReviewRequestDraft)
from reviewboard.reviews.signals import (reply_publishing,
                                         review_publishing,
                                         review_request_closed,
                                         review_request_publishing,
                                         review_request_reopened)
from reviewboard.site.urlresolvers import local_site_reverse

from rbbz.auth import BugzillaBackend
from rbbz.bugzilla import Bugzilla
from rbbz.diffs import build_plaintext_review
from rbbz.errors import (BugzillaError,
                         ConfidentialBugError,
                         InvalidBugIdError)
from rbbz.middleware import BugzillaCookieAuthMiddleware
from rbbz.models import (BugzillaUserMap,
                         get_or_create_bugzilla_users)
from rbbz.resources import bugzilla_cookie_login_resource


REVIEWID_RE = re.compile('bz://(\d+)/[^/]+')

AUTO_CLOSE_DESCRIPTION = """
Discarded automatically because parent review request was discarded.
"""

AUTO_SUBMITTED_DESCRIPTION = """
Submitted because the parent review request was submitted.
"""

NEVER_USED_DESCRIPTION = """
Discarded because this review request ended up not being needed.
"""

OBSOLETE_DESCRIPTION = """
Discarded because this change is no longer required.
"""

# Extra data fields which should be automatically copied from
# the draft to the review request on publish.
DRAFTED_EXTRA_DATA_KEYS = [
    'p2rb.identifier',
    'p2rb.commit_id',
    'p2rb.commits',
]


class BugzillaExtension(Extension):
    middleware = [BugzillaCookieAuthMiddleware]

    resources = [
        bugzilla_cookie_login_resource,
    ]

    def initialize(self):
        AuthBackendHook(self, BugzillaBackend)
        SignalHook(self, pre_delete, on_draft_pre_delete)
        SignalHook(self, review_request_publishing,
                   on_review_request_publishing)
        SignalHook(self, review_publishing, on_review_publishing)
        SignalHook(self, reply_publishing, on_reply_publishing)
        SignalHook(self, review_request_closed,
                   on_review_request_closed_discarded)
        SignalHook(self, review_request_closed,
                   on_review_request_closed_submitted)
        SignalHook(self, review_request_reopened, on_review_request_reopened)


def review_or_request_url(review_or_request, site=None, siteconfig=None):
    if not site:
        site = Site.objects.get_current()

    if not siteconfig:
        siteconfig = SiteConfiguration.objects.get_current()

    return '%s://%s%s%s' % (
        siteconfig.get('site_domain_method'), site.domain,
        local_site_reverse('root').rstrip('/'),
        review_or_request.get_absolute_url())


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

    for child in gen_rrs_by_extra_data_key(review_request, 'unpublished_rids'):
        child.close(ReviewRequest.DISCARDED,
                    user=user,
                    description=NEVER_USED_DESCRIPTION)

    review_request.extra_data['p2rb.discard_on_publish_rids'] = '[]'
    review_request.extra_data['p2rb.unpublished_rids'] = '[]'
    review_request.save()


@simple_decorator
def bugzilla_to_publish_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BugzillaError as e:
            raise PublishError('Bugzilla error: %s' % e.msg)
    return _transform_errors


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
    if not is_review_request_pushed(review_request):
        return

    # The reviewid passed through p2rb is, for Mozilla's instance anyway,
    # bz://<bug id>/<irc nick>.
    reviewid = review_request_draft.extra_data.get('p2rb.identifier', None)
    m = REVIEWID_RE.match(reviewid)

    if not m:
        raise InvalidBugIdError('<unknown>')

    bug_id = m.group(1)
    using_bugzilla = we_are_using_bugzilla()
    try:
        bug_id = int(bug_id)
    except (TypeError, ValueError):
        raise InvalidBugIdError(bug_id)

    if using_bugzilla:
        b = Bugzilla(user.bzlogin, user.bzcookie)

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

    # At this point, we know that the bug ID that we've got
    # is valid and accessible.
    review_request_draft.bugs_closed = str(bug_id)

    # The review request exposes a list of usernames for reviewers. We need
    # to convert these to Bugzilla emails in order to make the request into
    # Bugzilla.
    #
    # It may seem like there is a data syncing problem here where usernames may
    # get out of sync with the reality from Bugzilla. Fortunately, Review Board
    # is smarter than that. Internally, the target_people list is stored with
    # foreign keys into the numeric primary key of the user table. If the
    # RB username changes, this won't impact target_people nor the stored
    # mapping to the numeric Bugzilla ID, which is immutable.
    #
    # But we do have a potential data syncing problem with the stored email
    # address. Review Board's stored email address could be stale. So instead
    # of using it directly, we query Bugzilla and map the stored, immutable
    # numeric Bugzilla userid into an email address. This lookup could be
    # avoided if Bugzilla accepted a numeric userid in the requestee parameter
    # when modifying an attachment.
    reviewers = set()

    for u in review_request_draft.target_people.all():
        if not using_bugzilla:
            reviewers.append(u.get_username())

        bum = BugzillaUserMap.objects.get(user=u)

        user_data = b.get_user_from_userid(bum.bugzilla_user_id)

        # Since we're making the API call, we might as well ensure the local
        # database is up to date.
        users = get_or_create_bugzilla_users(user_data)
        reviewers.add(users[0].email)

    # Don't make attachments for child review requests, otherwise,
    # Bugzilla gets inundatated with lots of patches, and the squashed
    # one is the only one we want to post there.
    if is_review_request_squashed(review_request):
        comment = review_request_draft.description

        if (review_request_draft.changedesc and
            review_request_draft.changedesc.text):
            if not comment.endswith('\n'):
                comment += '\n'

            comment += '\n%s' % review_request_draft.changedesc.text

        if using_bugzilla:
            b.post_rb_url(bug_id,
                          review_request.id,
                          review_request_draft.summary,
                          comment,
                          review_or_request_url(review_request),
                          reviewers)

        unpublished_rids = json.loads(
            review_request.extra_data['p2rb.unpublished_rids'])
        discard_on_publish_rids = json.loads(
            review_request.extra_data['p2rb.discard_on_publish_rids'])

        # Publish any draft commits that have drafts. This will already include
        # items that are in unpublished_rids, so we'll remove anything we publish
        # out of unpublished_rids.
        for child in gen_child_rrs(review_request_draft):
            if child.get_draft(user=user) or not child.public:
                child.publish(user=user)
                id_str = str(child.id)
                if id_str in unpublished_rids:
                    unpublished_rids.remove(id_str)

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


@bugzilla_to_publish_errors
def on_review_publishing(user, review, **kwargs):
    review_request = review.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    site = Site.objects.get_current()
    siteconfig = SiteConfiguration.objects.get_current()
    comment = build_plaintext_review(review,
                                     review_or_request_url(review, site,
                                                           siteconfig),
                                     {"user": user})
    b = Bugzilla(user.bzlogin, user.bzcookie)

    rr_url = review_or_request_url(review_request, site, siteconfig)

    if review.ship_it and is_review_request_squashed(review_request):
        b.r_plus_attachment(bug_id, review.user.email, comment, rr_url)
    else:
        cancelled = b.cancel_review_request(bug_id, review.user.email,
            rr_url, comment)
        if not cancelled and comment:
            b.post_comment(bug_id, comment)

@bugzilla_to_publish_errors
def on_reply_publishing(user, reply, **kwargs):
    review_request = reply.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    b = Bugzilla(user.bzlogin, user.bzcookie)

    url = review_or_request_url(reply)
    comment = build_plaintext_review(reply, url, {"user": user})
    b.post_comment(bug_id, comment)


def on_review_request_closed_discarded(user, review_request, type, **kwargs):
    if (not is_review_request_squashed(review_request) or
        type != ReviewRequest.DISCARDED):
        return

    # close_child_review_requests will call save on this review request, so
    # we don't have to worry about it.
    review_request.commit = None

    close_child_review_requests(user, review_request, ReviewRequest.DISCARDED,
                                  AUTO_CLOSE_DESCRIPTION)

    b = Bugzilla(user.bzlogin, user.bzcookie)
    bug = int(review_request.get_bug_list()[0])
    url = review_or_request_url(review_request)
    b.obsolete_review_attachments(bug, url)

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
                                           'unpublished_rids'):
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
            commit_id=identifier)
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


def gen_child_rrs(review_request):
    """ Generate child review requests.

    For some review request (draft or normal), that has a p2rb.commits
    extra_data field, we yield the child review requests belonging to
    the rids in that field.

    If a review request is not found for the listed ID, get_rr_for_id will
    log this, and we'll skip that ID.
    """
    key = 'p2rb.commits'
    if not key in review_request.extra_data:
        return

    commit_tuples = json.loads(review_request.extra_data[key])
    for commit_tuple in commit_tuples:
        child = get_rr_for_id(commit_tuple[1])
        if child:
            yield child


def gen_rrs_by_extra_data_key(review_request, key):
    key = 'p2rb.' + key
    if not key in review_request.extra_data:
        return

    return gen_rrs_by_rids(json.loads(review_request.extra_data[key]))


def gen_rrs_by_rids(rids):
    for rid in rids:
        review_request = get_rr_for_id(rid)
        if review_request:
            yield review_request


def get_rr_for_id(rid):
    try:
        return ReviewRequest.objects.get(pk=rid)
    except ReviewRequest.DoesNotExist:
        logging.error('Could not retrieve child review request with '
                      'rid %s because it does not appear to exist.'
                      % rid)


def we_are_using_bugzilla():
    siteconfig = SiteConfiguration.objects.get_current()
    return siteconfig.settings.get("auth_backend", "builtin") == "bugzilla"
