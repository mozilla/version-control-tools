# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import factory
from django.contrib.auth.models import User, Permission


class BaseFactory(factory.django.DjangoModelFactory):
    # Django models are compared for equivalence using the object.id
    # attribute, not by comparing the value of id(object).  If we don't
    # include an id/pk field, then it defaults to 'None' for these unsaved DB
    # objects.  That in-turn causes the Django model comparison to
    # incorrectly return 'True' when comparing unsaved DB objects with '=='.
    id = factory.Sequence(int)


class UserFactory(BaseFactory):
    class Meta:
        model = User
        strategy = factory.BUILD_STRATEGY

    username = factory.Faker('word')

    class Params:
        permissions = []

    @factory.post_generation
    def permissions(user, create, extracted, **kwargs):
        perms_list = extracted
        for p in perms_list:
            perm = Permission.objects.get(codename=p)
            user.user_permissions.add(perm)