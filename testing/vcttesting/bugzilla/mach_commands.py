# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import os
import sys
import xmlrpclib

import bugsy
import requests
import yaml

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

    @Command('update-user-fullname', category='bugzilla',
            description='Update the fullname field of a user')
    @CommandArgument('email', help='The email of the user to update')
    @CommandArgument('name', help='The new name for the user')
    def update_user_fullname(self, email, name):
        h = self.proxy.User.update({
            'names': [email],
            'full_name': name,
        })
        print('updated user %s' % h['users'][0]['id'])

    @Command('update-user-email', category='bugzilla',
            description='Update the email of a user')
    @CommandArgument('old_email', help='The email of the user to update')
    @CommandArgument('new_email', help='The new email for the user')
    def update_user_email(self, old_email, new_email):
        h = self.proxy.User.update({
            'names': [old_email],
            'email': new_email,
        })
        print('updated user %s' % h['users'][0]['id'])

    @Command('update-user-login-denied-text', category='bugzilla',
            description='Update the login denied text for a user')
    @CommandArgument('email', help='The email of the user to update')
    @CommandArgument('text', help='The login denied text for the user')
    def update_user_login_denied_text(self, email, text):
        h = self.proxy.User.update({
            'names': [email],
            'login_denied_text': text,
        })
        print('updated user %s' % h['users'][0]['id'])

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

    @Command('dump-bug', category='bugzilla',
            description='Dump a representation of a bug')
    @CommandArgument('bugs', nargs='+', help='Bugs to dump')
    def dump_bug(self, bugs):
        data = {}
        for bid in bugs:
            bug = self.client.get(bid)

            d = dict(
                summary=bug.summary,
                comments=[],
            )
            for comment in bug.get_comments():
                d['comments'].append(dict(
                    id=comment.id,
                    text=comment.text,
                ))

            r = self.client.request('bug/%s/attachment' % bid).json()
            for a in r['bugs'].get(bid, []):
                flags = []
                for f in a['flags']:
                    flags.append(dict(
                        id=f['id'],
                        name=f['name'],
                        requestee=f.get('requestee'),
                        setter=f['setter'],
                        status=f['status'],
                    ))

                at = d.setdefault('attachments', [])
                at.append(dict(
                    id=a['id'],
                    attacher=a['attacher'],
                    content_type=a['content_type'],
                    description=a['description'],
                    summary=a['summary'],
                    data=base64.b64decode(a['data']),
                    flags=flags))

            key = 'Bug %s' % bid
            data[key] = d

        print(yaml.safe_dump(data, default_flow_style=False).rstrip())

