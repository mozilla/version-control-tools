# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator
from reviewboard.reviews.errors import PublishError
from reviewboard.reviews.signals import (review_request_publishing,
                                         review_publishing, reply_publishing)
from reviewboard.site.urlresolvers import local_site_reverse

from rbbz.bugzilla import Bugzilla
from rbbz.errors import BugzillaError, InvalidBugIdError, InvalidReviewerError

def review_request_url(review_request, site=None, siteconfig=None):
    if not site:
        site = Site.objects.get_current()

    if not siteconfig:
        siteconfig = SiteConfiguration.objects.get_current()

    return '%s://%s%s%s' % (
        siteconfig.get('site_domain_method'), site.domain,
        local_site_reverse('root').rstrip('/'),
        review_request.get_absolute_url())


@simple_decorator
def bugzilla_to_publish_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BugzillaError as e:
            raise PublishError(e.msg)
    return _transform_errors


@bugzilla_to_publish_errors
def publish_review_request(user, review_request_draft, **kwargs):
    try:
        bug_id = int(review_request_draft.get_bug_list()[0])
    except (IndexError, TypeError, ValueError):
        raise InvalidBugIdError

    reviewer = review_request_draft.target_people.first()
    if reviewer is None:
        raise InvalidReviewerError

    b = Bugzilla(user.bzlogin, user.bzcookie)
    b.post_rb_url(review_request_draft.summary, bug_id,
                  review_request_url(review_request_draft.get_review_request()),
                  reviewer.get_username())


def publish_review(user, review, **kwargs):
    if review.ship_it:
        try:
            bug_id = int(review.review_request.get_bug_list()[0])
        except (IndexError, TypeError, ValueError):
            return

        site = Site.objects.get_current()
        siteconfig = SiteConfiguration.objects.get_current()

        b = Bugzilla(user.bzlogin, user.bzcookie)
        attachments = b.get_rb_attachments(bug_id)

        for a in attachments:
            if (a['reviewer'] == review.user.username and
                a['url'] == review_request_url(review.review_request, site,
                                               siteconfig)):
                b.r_plus_attachment(a['id'])
                break


def publish_reply(user, reply, **kwargs):
    pass


review_request_publishing.connect(publish_review_request)
review_publishing.connect(publish_review)
reply_publishing.connect(publish_reply)


def get_or_create_bugzilla_users(user_data):
    # All users will have a stored password of "!", which Django uses to
    # indicate an invalid password.
    users_db = []

    for user in user_data['users']:
        username = user['email']
        real_name = user['real_name']
        can_login = user['can_login']
        modified = False

        try:
            user_db = User.objects.get(username=username)
        except User.DoesNotExist:
            user_db = User(username=username, password='!',
                           first_name=real_name, email=username,
                           is_active=can_login)
            modified = True
        else:
            if user_db.first_name != real_name:
                user_db.first_name = real_name
                modified = True

            if user_db.is_active != can_login:
                user_db.is_active = can_login
                modified = True

        if modified:
            user_db.save()

        users_db.append(user_db)
    return users_db

