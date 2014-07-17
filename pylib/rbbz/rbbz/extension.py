# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from django.contrib.sites.models import Site

from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import AuthBackendHook, SignalHook
from reviewboard.reviews.errors import PermissionError, PublishError
from reviewboard.reviews.models import ReviewRequest
from reviewboard.reviews.signals import (reply_publishing,
                                         review_publishing,
                                         review_request_closed,
                                         review_request_publishing)
from reviewboard.site.urlresolvers import local_site_reverse

from rbbz.auth import BugzillaBackend
from rbbz.bugzilla import Bugzilla
from rbbz.diffs import build_plaintext_review
from rbbz.errors import (BugzillaError,
                         ConfidentialBugError,
                         InvalidBugIdError)
from rbbz.middleware import BugzillaCookieAuthMiddleware


BZIMPORT_PREFIX = "bz://"
AUTO_CLOSE_DESCRIPTION = """
Discarded automatically because parent review request was discarded.
"""


class BugzillaExtension(Extension):
    middleware = [BugzillaCookieAuthMiddleware]

    def initialize(self):
        AuthBackendHook(self, BugzillaBackend)
        SignalHook(self, review_request_publishing,
                   on_review_request_publishing)
        SignalHook(self, review_publishing, on_review_publishing)
        SignalHook(self, reply_publishing, on_reply_publishing)
        SignalHook(self, review_request_closed, on_review_request_closed)


def review_request_url(review_request, site=None, siteconfig=None):
    if not site:
        site = Site.objects.get_current()

    if not siteconfig:
        siteconfig = SiteConfiguration.objects.get_current()

    return '%s://%s%s%s' % (
        siteconfig.get('site_domain_method'), site.domain,
        local_site_reverse('root').rstrip('/'),
        review_request.get_absolute_url())


def is_review_request_pushed(review_request):
    return str(review_request.extra_data.get('p2rb', False)) == "True"


def is_review_request_squashed(review_request):
    squashed = str(review_request.extra_data.get('p2rb.is_squashed', False))
    return squashed == "True"


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
    review_request = review_request_draft.get_review_request()

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    # The reviewid passed through p2rb is, for Mozilla's instance anyway, also
    # the bug ID.
    bug_id = review_request_draft.extra_data.get('p2rb.identifier', None)

    if bug_id.startswith(BZIMPORT_PREFIX):
        bug_id = bug_id[len(BZIMPORT_PREFIX):]

    try:
        bug_id = int(bug_id)
    except (TypeError, ValueError):
        raise InvalidBugIdError(bug_id)

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

    reviewers = [x.get_username() for x in
                 review_request_draft.target_people.all()]

    # Don't make attachments for child review requests, otherwise,
    # Bugzilla gets inundatated with lots of patches, and the squashed
    # one is the only one we want to post there.
    if is_review_request_squashed(review_request):
        b.post_rb_url(bug_id,
                      review_request.id,
                      review_request_draft.summary,
                      review_request_draft.description,
                      review_request_url(review_request),
                      reviewers)
        # Publish and child review requests that are either not
        # public, or have drafts.
        for child in generate_child_review_requests(review_request):
            try:
                if child.status == ReviewRequest.DISCARDED:
                    child.reopen(user=user)
                if child.get_draft(user=user) or not child.public:
                    child.publish(user=user)
            except PermissionError as e:
                logging.error('Could not reopen or publish child review '
                              'request with id %s because of error %s'
                              % (child.id, e))


def on_review_publishing(user, review, **kwargs):
    review_request = review.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    site = Site.objects.get_current()
    siteconfig = SiteConfiguration.objects.get_current()
    b = Bugzilla(user.bzlogin, user.bzcookie)

    b.post_comment(bug_id, build_plaintext_review(review, {"user": user}))

    if review.ship_it and is_review_request_squashed(review_request):
        b.r_plus_attachment(bug_id, review.user.username,
                            review_request_url(review_request, site,
                                               siteconfig))


def on_reply_publishing(user, reply, **kwargs):
    review_request = reply.review_request

    # skip review requests that were not pushed
    if not is_review_request_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    b = Bugzilla(user.bzlogin, user.bzcookie)

    b.post_comment(bug_id, build_plaintext_review(reply, {"user": user}))


def on_review_request_closed(user, review_request, type, **kwargs):
    if (is_review_request_squashed(review_request) and
            type == ReviewRequest.DISCARDED):
        # At the point of discarding, it's possible that if this review
        # request was never published, that most of the fields are empty
        # (See https://code.google.com/p/reviewboard/issues/detail?id=3465).
        # Luckily, the extra_data is still around, and more luckily, it's
        # not exposed in the UI for user-meddling. We can find all of the
        # child review requests via extra_data.p2rb.commits.
        for child in generate_child_review_requests(review_request):
            child.close(ReviewRequest.DISCARDED,
                        user=user,
                        description=AUTO_CLOSE_DESCRIPTION)

        # Next, we clear out the commit_id on the squashed review request
        # so that someone can post follow-up work with the same review
        # identifier in the future. This value is, however, still being
        # stored in extra_data under "p2rb.identifier".
        review_request.commit = None
        review_request.save()


def generate_child_review_requests(squashed_review_request):
    if not is_review_request_squashed(squashed_review_request):
        return

    commits = squashed_review_request.extra_data['p2rb.commits']
    if commits:
        commits = json.loads(commits)
        for commit_tuple in commits:
            child_commit_id = commit_tuple[0]
            child_request_id = commit_tuple[1]
            try:
                child = ReviewRequest.objects.get(pk=child_request_id)
                yield child
            except ReviewRequest.DoesNotExist:
                logging.error('Could not retrieve child review request '
                              'with id %s belonging to commit %s because '
                              'it does not appear to exist.'
                              % (child_request_id, child_commit_id))
