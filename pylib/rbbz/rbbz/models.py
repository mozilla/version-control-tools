# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth.models import User
from django.db import models


class BugzillaUserMap(models.Model):
    user = models.OneToOneField(User)
    bugzilla_user_id = models.IntegerField(unique=True, db_index=True)


def get_or_create_bugzilla_users(user_data):
    # All users will have a stored password of "!", which Django uses to
    # indicate an invalid password.
    users = []

    for user in user_data['users']:
        bz_user_id = user['id']
        email = user['email']
        real_name = user['real_name']
        can_login = user['can_login']

        try:
            bugzilla_user_map = BugzillaUserMap.objects.get(
                bugzilla_user_id=bz_user_id)
        except BugzillaUserMap.DoesNotExist:
            user = User(username=bz_user_id, password='!', first_name=real_name,
                        email=email, is_active=can_login)
            user.save()
            bugzilla_user_map = BugzillaUserMap(user=user,
                                                bugzilla_user_id=bz_user_id)
            bugzilla_user_map.save()
        else:
            modified = False
            user = bugzilla_user_map.user

            if user.username != bz_user_id:
                user.username = bz_user_id
                modified = True

            if user.email != email:
                user.email = email
                modified = True

            if user.first_name != real_name:
                user.first_name = real_name
                modified = True

            if user.is_active != can_login:
                user.is_active = can_login
                modified = True

            if modified:
                user.save()

        users.append(user)
    return users
