# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.sites.models import Site

from djblets.siteconfig.models import SiteConfiguration

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import AuthBackendHook, SignalHook
from reviewboard.reviews.signals import (
    reply_publishing,
    review_publishing,
)

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import (
    bugzilla_to_publish_errors,
)
from mozreview.errors import (
    ParentShipItError,
)
from mozreview.extra_data import (
    MOZREVIEW_KEY,
    SQUASHED_KEY,
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
        SignalHook(self, review_publishing, on_review_publishing,
                   sandbox_errors=False)
        SignalHook(self, reply_publishing, on_reply_publishing,
                   sandbox_errors=False)


def get_reply_url(reply, site=None, siteconfig=None):
    """ Get the URL for a reply to a review.

    Since replies can have multiple comments, we can't link to a specific
    comment, so we link to the parent review which the reply is targeted at.
    """
    return get_obj_url(reply.base_reply_to, site=site, siteconfig=siteconfig)


def is_review_request_pushed(review_request):
    return str(review_request.extra_data.get(MOZREVIEW_KEY, False)) == "True"


def is_review_request_squashed(review_request):
    squashed = str(review_request.extra_data.get(SQUASHED_KEY, False))
    return squashed == "True"


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
