# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

from vcttesting.bugzilla import Bugzilla

@CommandProvider
class BugzillaCommands(object):
    def __init__(self, context):
        self.base_url = os.environ['BUGZILLA_URL']
        username = os.environ['BUGZILLA_USERNAME']
        password = os.environ['BUGZILLA_PASSWORD']

        self.b = Bugzilla(self.base_url, username=username, password=password)

    @Command('create-bug', category='bugzilla',
            description='Create a new bug')
    @CommandArgument('product', help='Product to create bug in')
    @CommandArgument('component', help='Component to create bug in')
    @CommandArgument('summary', help='Bug summary')
    def create_bug(self, product, component, summary):
        self.b.create_bug(product, component, summary)

    @Command('create-bug-range', category='bugzilla',
            description='Create multiple bugs at once')
    @CommandArgument('product', help='Product to create bugs in')
    @CommandArgument('component', help='Component to create bugs in')
    @CommandArgument('count', type=int, help='The number of bugs to create')
    def create_bug_range(self, product, component, count):
        total, first, last = self.b.create_bug_range(product, component, count)
        print('created bugs %d to %d' % (first, last))

    @Command('create-group', category='bugzilla',
            description='Create a Bugzilla group')
    @CommandArgument('group', help='Name of the group to create')
    @CommandArgument('description', help='Description of the group to create')
    def create_group(self, group, description):
        self.b.create_group(group, description)

    @Command('create-user', category='bugzilla',
            description='Create a user')
    @CommandArgument('email', help='The email / username of the user to create')
    @CommandArgument('password', help='The password to use for the user')
    @CommandArgument('name', help='The full name of the user being created')
    def create_user(self, email, password, name):
        u = self.b.create_user(email, password, name)
        print('created user %s' % u['id'])

    @Command('update-user-fullname', category='bugzilla',
            description='Update the fullname field of a user')
    @CommandArgument('email', help='The email of the user to update')
    @CommandArgument('name', help='The new name for the user')
    def update_user_fullname(self, email, name):
        u = self.b.update_user_fullname(email, name)
        print('updated user %s' % u['users'][0]['id'])

    @Command('update-user-email', category='bugzilla',
            description='Update the email of a user')
    @CommandArgument('old_email', help='The email of the user to update')
    @CommandArgument('new_email', help='The new email for the user')
    def update_user_email(self, old_email, new_email):
        u = self.b.update_user_email(old_email, new_email)
        print('updated user %s' % u['users'][0]['id'])

    @Command('update-user-login-denied-text', category='bugzilla',
            description='Update the login denied text for a user')
    @CommandArgument('email', help='The email of the user to update')
    @CommandArgument('text', help='The login denied text for the user')
    def update_user_login_denied_text(self, email, text):
        u = self.b.update_user_login_denied_text(email, text)
        print('updated user %s' % u['users'][0]['id'])

    @Command('create-login-cookie', category='bugzilla',
            description='Create a login cookie from credentials')
    def create_login_cookie(self):
        login, cookie = self.b.create_login_cookie()
        print('%s %s' % (login, cookie))

    @Command('dump-bug', category='bugzilla',
            description='Dump a representation of a bug')
    @CommandArgument('bugs', nargs='+', help='Bugs to dump')
    def dump_bug(self, bugs):
        print(self.b.serialize_bugs(bugs))
