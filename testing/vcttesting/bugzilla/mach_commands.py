# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import xmlrpclib

import bugsy
import requests

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

from rbbz.transports import bugzilla_transport

@CommandProvider
class BugzillaCommands(object):
    def __init__(self, context):
        url = os.environ['BUGZILLA_URL'] + '/rest'
        self.base_url = os.environ['BUGZILLA_URL']
        username = os.environ['BUGZILLA_USERNAME']
        password = os.environ['BUGZILLA_PASSWORD']

        self.username = username
        self.password = password

        xmlrpcurl = os.environ['BUGZILLA_URL'] + '/xmlrpc.cgi'
        transport = bugzilla_transport(xmlrpcurl)

        proxy = xmlrpclib.ServerProxy(xmlrpcurl, transport)
        proxy.User.login({'login': username, 'password': password})

        client = bugsy.Bugsy(username=username, password=password,
                bugzilla_url=url)

        self.proxy = proxy
        self.client = client

    @Command('create-bug', category='bugzilla',
            description='Create a new bug')
    @CommandArgument('product', help='Product to create bug in')
    @CommandArgument('component', help='Component to create bug in')
    @CommandArgument('summary', help='Bug summary')
    def create_bug(self, product, component, summary):
        bug = bugsy.Bug(self.client, product=product, component=component,
                summary=summary)
        self.client.put(bug)

    @Command('create-bug-range', category='bugzilla',
            description='Create multiple bugs at once')
    @CommandArgument('product', help='Product to create bugs in')
    @CommandArgument('component', help='Component to create bugs in')
    @CommandArgument('upper', type=int, help='The highest bug # to create')
    def create_bug_range(self, product, component, upper):
        existing = self.client.search_for.search()
        ids = [int(b['id']) for b in existing]
        ids.append(1)
        maxid = max(ids)

        count = 0
        for i in range(maxid, upper + 1):
            count += 1
            bug = bugsy.Bug(self.client, product=product, component=component,
                    summary='Range %d' % i)
            self.client.put(bug)

        print('created %d bugs' % count)

    @Command('create-group', category='bugzilla',
            description='Create a Bugzilla group')
    @CommandArgument('group', help='Name of the group to create')
    @CommandArgument('description', help='Description of the group to create')
    def create_group(self, group, description):
        # Adding every user to every group is wrong. This is a quick hack to
        # work around bug 1079463.
        h = self.proxy.Group.create({
            'name': group,
            'description': description,
            'user_regexp': '.*',
        })

    @Command('create-user', category='bugzilla',
            description='Create a user')
    @CommandArgument('email', help='The email / username of the user to create')
    @CommandArgument('password', help='The password to use for the user')
    @CommandArgument('name', help='The full name of the user being created')
    def create_user(self, email, password, name):
        h = self.proxy.User.create({
            'email': email,
            'password': password,
            'full_name': name,
        })
        print('created user %s' % h['id'])

    @Command('create-login-cookie', category='bugzilla',
            description='Create a login cookie from credentials')
    def create_login_cookie(self):
        # We simulate a browser's HTML interaction with Bugzilla to obtain a
        # login cookie. Is there a better way?
        url = self.base_url + '/'
        r = requests.get(url + '/')
        cookies = dict(r.cookies)

        params = {
            'Bugzilla_login': self.username,
            'Bugzilla_password': self.password,
            'Bugzilla_login_token': '',
        }
        r = requests.post(url + '/index.cgi', params=params, cookies=cookies)
        if r.status_code != 200:
            raise Exception('Non-200 response from Bugzilla. Proper credentials?')

        login = r.cookies['Bugzilla_login']
        cookie = r.cookies['Bugzilla_logincookie']
        print('%s %s' % (login, cookie))
