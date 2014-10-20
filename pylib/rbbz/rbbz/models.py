# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

from django.contrib.auth.models import User
from django.db import models
from reviewboard.accounts.models import Profile

# Note that Review Board only allows a subset of legal IRC-nick characters.
# Specifically, Review Board does not allow [ \ ] ^ ` { | }
# Anyone with those in their :ircnicks will have them truncated at the last
# legal character.  Not great, but we can later implement a UI for letting
# people change their usernames in Review Board.
BZ_IRCNICK_RE = re.compile(':([A-Za-z0-9_\-\.]+)')

class BugzillaUserMap(models.Model):
    user = models.OneToOneField(User)
    bugzilla_user_id = models.IntegerField(unique=True, db_index=True)


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

            profile = Profile.objects.get_or_create(user=user)[0]
            if not profile.is_private:
                profile.is_private = True
                profile.save()

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
