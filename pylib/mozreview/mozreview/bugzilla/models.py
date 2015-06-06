# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import re

from django.contrib.auth.models import User
from django.db import models, transaction
from reviewboard.accounts.models import Profile
from reviewboard.reviews.models import ReviewRequest


# Note that Review Board only allows a subset of legal IRC-nick characters.
# Specifically, Review Board does not allow [ \ ] ^ ` { | }
# Anyone with those in their :ircnicks will have them truncated at the last
# legal character.  Not great, but we can later implement a UI for letting
# people change their usernames in Review Board.
BZ_IRCNICK_RE = re.compile(':([A-Za-z0-9_\-\.]+)')


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

        ircnick_match = BZ_IRCNICK_RE.search(real_name)

        if ircnick_match:
            username = ircnick_match.group(1)
        else:
            username = placeholder_username(email, bz_user_id)

        try:
            bugzilla_user_map = BugzillaUserMap.objects.get(
                bugzilla_user_id=bz_user_id)
        except BugzillaUserMap.DoesNotExist:
            user = User(username=username, password='!', first_name=real_name,
                        email=email, is_active=can_login)

            try:
                user.save()
            except:
                # Blanket exceptions are terrible, but there appears to
                # be no way to catch a generic IntegrityError.
                user.username = placeholder_username(email, bz_user_id)
                user.save()

            bugzilla_user_map = BugzillaUserMap(user=user,
                                                bugzilla_user_id=bz_user_id)
            bugzilla_user_map.save()

            profile = Profile.objects.get_or_create(user=user)[0]
            if not profile.is_private:
                profile.is_private = True
                profile.save()
        else:
            modified = False
            user = bugzilla_user_map.user

            if user.username != username:
                user.username = username
                modified = True

            if user.email != email:
                user.email = email
                modified = True

            if user.first_name != real_name:
                user.first_name = real_name
                modified = True

            # Note that users *must* be disabled in Bugzilla and *cannot*
            # be disabled in Review Board, since, if user.is_active is False,
            # we can't tell if this was a result of can_login going False
            # at some previous time or the action of a Review Board admin.
            if user.is_active != can_login:
                user.is_active = can_login
                modified = True

            if modified:
                try:
                    user.save()
                except:
                    # Blanket exceptions are terrible, but there appears to
                    # be no way to catch a generic IntegrityError.
                    user.username = placeholder_username(email, bz_user_id)
                    user.save()

        users.append(user)
    return users


def set_bugzilla_api_key(user, api_key):
    """Assigns a Bugzilla API key to a user.

    The user must exist before this function is called.
    """
    bugzilla_user_map = BugzillaUserMap.objects.get(user=user)
    if bugzilla_user_map.api_key != api_key:
        bugzilla_user_map.api_key = api_key
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
    MAX_LOGIN_DIFFERENCE = datetime.timedelta(0,1) # 1 second
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
