# coding=utf-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging
import re

from django.contrib.auth.models import User
from django.db import models, transaction
from mozautomation.commitparser import BMO_IRC_NICK_RE
from reviewboard.accounts.models import Profile
from reviewboard.reviews.models import ReviewRequest

logger = logging.getLogger(__name__)


class BugzillaUserMap(models.Model):
    """Holds Bugzilla-related data about Review Board users.

    This model is deprecated in favour of MozReviewUserProfile; please put
    any future user data there.
    """
    user = models.OneToOneField(User)
    bugzilla_user_id = models.IntegerField(unique=True, db_index=True)
    api_key = models.CharField(max_length=40, null=True)

    class Meta:
        app_label = 'mozreview'


class UnverifiedBugzillaApiKey(models.Model):
    """Holds unverified Bugzilla API keys.

    This table holds API keys sent from Bugzilla until we are able to verify
    them, after which they are removed from this table.
    """
    bmo_username = models.CharField(max_length=255, db_index=True)
    api_key = models.CharField(max_length=40)
    timestamp = models.DateTimeField(auto_now_add=True)
    callback_result = models.CharField(max_length=36)

    class Meta:
        app_label = 'mozreview'


def placeholder_username(email, bz_user_id):
    return '%s+%s' % (email.split('@')[0], bz_user_id)


def get_or_create_bugzilla_users(user_data):
    # All users will have a stored password of "!", which Django uses to
    # indicate an invalid password.
    users = []

    for user in user_data['users']:
        bz_user_id = user['id']
        email = user['email']
        real_name = user['real_name']
        can_login = user['can_login']

        # remove emoji from real_name; something between rb, djano, and mysql breaks
        emoji_re = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U000E0001"
            u"\U000E0020-\U000E007F"
            "]+",
            flags=re.UNICODE,
        )
        real_name = emoji_re.sub("", real_name)

        ircnick_match = BMO_IRC_NICK_RE.search(real_name)

        if ircnick_match:
            username = ircnick_match.group(1)
        else:
            username = placeholder_username(email, bz_user_id)

        try:
            bugzilla_user_map = BugzillaUserMap.objects.get(
                bugzilla_user_id=bz_user_id)
        except BugzillaUserMap.DoesNotExist:
            logger.info('bugzilla user %s/%s not present; creating %s' % (
                        bz_user_id, email, username))
            user = User(username=username, password='!', first_name=real_name,
                        email=email, is_active=can_login)

            try:
                # Django kind of "corrupts" the DB transaction when an
                # integrity error occurs. So, we need to wrap in a
                # sub-transaction to prevent the "corruption" from
                # tainting the outer transaction.
                with transaction.atomic():
                    user.save()
            except:
                # Blanket exceptions are terrible, but there appears to
                # be no way to catch a generic IntegrityError since SQLite
                # and MySQL apparently share different exception class
                # hierarchies?!
                user.username = placeholder_username(email, bz_user_id)
                logger.info('could not create user %s; trying %s' % (
                            username, user.username))
                user.save()

            bugzilla_user_map = BugzillaUserMap(user=user,
                                                bugzilla_user_id=bz_user_id)
            bugzilla_user_map.save()

            profile = Profile.objects.get_or_create(user=user)[0]
            if not profile.is_private:
                profile.is_private = True
                profile.save()

            logger.info('created user %s:%s from bugzilla user %s/%s/%s' % (
                user.id, user.username,
                bz_user_id, email, real_name
            ))
        else:
            modified = False
            user = bugzilla_user_map.user
            old_username = user.username

            if user.username != username:
                logger.info('updating username of %s from %s to %s' % (
                    user.id, user.username, username
                ))
                user.username = username

                try:
                    with transaction.atomic():
                        user.save()
                except:
                    # Blanket exceptions are terrible.
                    new_username = placeholder_username(email, bz_user_id)
                    if new_username != old_username:
                        logger.info('could not set preferred username to %s; '
                                    'updating username of %s from %s to %s' % (
                                        username, user.id, old_username,
                                        new_username))
                        user.username = new_username
                        user.save()
                    else:
                        logger.info('could not update username of %s; keeping '
                                    'as %s' % (user.id, old_username))
                        user.username = old_username

            if user.email != email:
                logger.info('updating email of %s:%s from %s to %s' % (
                    user.id, user.username, user.email, email
                ))
                user.email = email
                modified = True

            if user.first_name != real_name:
                logger.info('updating first name of %s:%s from %s to %s' % (
                    user.id, user.username, user.first_name, real_name
                ))
                user.first_name = real_name
                modified = True

            # Note that users *must* be disabled in Bugzilla and *cannot*
            # be disabled in Review Board, since, if user.is_active is False,
            # we can't tell if this was a result of can_login going False
            # at some previous time or the action of a Review Board admin.
            if user.is_active != can_login:
                logger.info('updating active of %s:%s to %s' % (
                    user.id, user.username, can_login
                ))
                user.is_active = can_login
                modified = True

            if modified:
                user.save()

        users.append(user)
    return users


def get_bugzilla_api_key(user):
    if not user or not user.is_authenticated():
        return None

    try:
        return BugzillaUserMap.objects.get(user=user).api_key
    except BugzillaUserMap.DoesNotExist:
        return None


def set_bugzilla_api_key(user, api_key):
    """Assigns a Bugzilla API key to a user.

    The user must exist before this function is called.
    """
    bugzilla_user_map = BugzillaUserMap.objects.get(user=user)
    if bugzilla_user_map.api_key != api_key:
        bugzilla_user_map.api_key = api_key
        logger.info('updating bugzilla api key for %s:%s' % (
            user.id, user.username
        ))
        bugzilla_user_map.save()


def prune_inactive_users(commit=False, verbose=False):
    """Delete inactive users.

    We will delete users which have not done any of the following:
    - created a review request
    - been asked to review a request
    - submitted a review
    - logged in since their account was created

    By default, this function will perform a dry run and will only
    commit the user deletion to the database if the commit argument
    is True.
    """
    MAX_LOGIN_DIFFERENCE = datetime.timedelta(0, 1)  # 1 second
    SPECIAL_USERNAMES = [
        'admin',
        'mozreview',
    ]
    SPECIAL_EMAILS = [
        'autoland@mozilla.bugs',
        'mozreview+python@mozilla-com.bugs',
    ]

    active_uids = set()
    print('Gathering active users.')
    # There's more efficient ways to do this. But we're optimized for one-time
    # uses, so performance isn't critical.
    for rr in ReviewRequest.objects.all():
        active_uids.add(rr.submitter.id)

        for u in rr.target_people.all():
            active_uids.add(u.id)

        for u in rr.participants:
            active_uids.add(u.id)

        draft = rr.get_draft()
        if draft:
            for u in draft.target_people.all():
                active_uids.add(u.id)

    print('%s active users after review request checks.' % len(active_uids))

    for u in User.objects.filter(email__in=SPECIAL_EMAILS):
        active_uids.add(u.id)

    print('%s active users after special email checks.' % len(active_uids))

    for u in User.objects.filter(username__in=SPECIAL_USERNAMES):
        active_uids.add(u.id)

    print('%s active users after special username checks.' % len(active_uids))

    for u in User.objects.all():
        if (u.date_joined - u.last_login) > MAX_LOGIN_DIFFERENCE:
            active_uids.add(u.id)

    print('%s active users after login time checks.' % len(active_uids))

    print('Detected %s active users.' % len(active_uids))

    if verbose:
        print('Active Users:')
        for u in User.objects.filter(id__in=active_uids).order_by('id',
                                                                  'email'):
            print('\t%s - %s - %s' % (u.id, u.email, u.first_name))

    print('Detected %s inactive users.' %
          User.objects.exclude(id__in=active_uids).count())

    if not commit:
        return

    print('Performing user deletion.')
    # Now delete all of the inactive users inside of
    # a transaction.
    with transaction.atomic():
        BugzillaUserMap.objects.exclude(user__id__in=active_uids).delete()

        from mozreview.models import MozReviewUserProfile
        MozReviewUserProfile.objects.exclude(user__id__in=active_uids).delete()

        while User.objects.exclude(id__in=active_uids).count():
            ids = User.objects.exclude(id__in=active_uids).values_list(
                'id', flat=True)[:500]
            User.objects.filter(id__in=list(ids)).delete()
