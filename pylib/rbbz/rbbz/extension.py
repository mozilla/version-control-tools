# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import (
    reply_publishing,
)

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import (
    bugzilla_to_publish_errors,
)
from mozreview.diffs import build_plaintext_review
from mozreview.extra_data import (
    is_pushed,
)
from mozreview.models import (
    get_bugzilla_api_key,
)
from mozreview.rb_utils import (
    get_obj_url,
)

logger = logging.getLogger(__name__)


class BugzillaExtension(Extension):

    def initialize(self):
        # Any abortable signal hooks that talk to Bugzilla should have
        # sandbox_errors=False, since we don't want to complete the action if
        # updating Bugzilla failed for any reason.
        SignalHook(self, reply_publishing, on_reply_publishing,
                   sandbox_errors=False)


def get_reply_url(reply, site=None, siteconfig=None):
    """ Get the URL for a reply to a review.

    Since replies can have multiple comments, we can't link to a specific
    comment, so we link to the parent review which the reply is targeted at.
    """
    return get_obj_url(reply.base_reply_to, site=site, siteconfig=siteconfig)


@bugzilla_to_publish_errors
def on_reply_publishing(user, reply, **kwargs):
    review_request = reply.review_request
    logger.info('Posting bugzilla reply for review request %s' % (
                review_request.id))

    # skip review requests that were not pushed
    if not is_pushed(review_request):
        return

    bug_id = int(review_request.get_bug_list()[0])
    b = Bugzilla(get_bugzilla_api_key(user))

    url = get_reply_url(reply)
    comment = build_plaintext_review(reply, url, {"user": user})
    b.post_comment(bug_id, comment)
