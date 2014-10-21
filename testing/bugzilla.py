#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This is a script for performing common Bugzilla operations from the command
# line. It is meant to support testing.

import base64
import os
import sys

import bugsy
import requests
import yaml
import xmlrpclib

from rbbz.transports import bugzilla_transport
from mach.main import Mach

HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, HERE)

def main(args):
    m = Mach(os.getcwd())
    m.define_category('bugzilla', 'Bugzilla',
        'Interface with Bugzilla', 50)
    import vcttesting.bugzilla.mach_commands

    legacy_actions = set([
        'create-bug-range',
        'dump-bug',
        'create-user',
        'update-user-fullname',
        'update-user-email',
        'update-user-login-denied-text',
        'create-group',
        'create-login-cookie',
    ])

    use_mach = True

    action = args[0]
    if action in legacy_actions:
        use_mach = False

    if use_mach:
        return m.run(args)

    url = os.environ['BUGZILLA_URL'] + '/rest'
    username = os.environ['BUGZILLA_USERNAME']
    password = os.environ['BUGZILLA_PASSWORD']

    xmlrpcurl = os.environ['BUGZILLA_URL'] + '/xmlrpc.cgi'
    transport = bugzilla_transport(xmlrpcurl)
    proxy = xmlrpclib.ServerProxy(xmlrpcurl, transport)
    proxy.User.login({'login': username, 'password': password})

    client = bugsy.Bugsy(username=username, password=password,
            bugzilla_url=url)

    action = args[0]

    if action == 'create-bug-range':
        product, component, upper = args[1:]

        existing = client.search_for.search()
        ids = [int(b['id']) for b in existing]
        ids.append(1)
        maxid = max(ids)

        count = 0
        for i in range(maxid, int(upper) + 1):
            count += 1
            bug = bugsy.Bug(client, product=product, component=component,
                    summary='Range %d' % i)
            foo = client.put(bug)

        print('created %d bugs' % count)

    elif action == 'dump-bug':
        data = {}
        for bid in args[1:]:
            bug = client.get(bid)

            d = dict(
                summary=bug.summary,
                comments=[],
            )
            for comment in bug.get_comments():
                d['comments'].append(dict(
                    id=comment.id,
                    text=comment.text,
                ))

            r = client.request('bug/%s/attachment' % bid).json()
            for a in r['bugs'].get(bid, []):
                at = d.setdefault('attachments', [])
                at.append(dict(
                    id=a['id'],
                    attacher=a['attacher'],
                    content_type=a['content_type'],
                    description=a['description'],
                    summary=a['summary'],
                    data=base64.b64decode(a['data'])))

            key = 'Bug %s' % bid
            data[key] = d

        print(yaml.safe_dump(data, default_flow_style=False).rstrip())

    elif action == 'create-user':
        email, password, name = args[1:]
        h = proxy.User.create({
            'email': email,
            'password': password,
            'full_name': name,
        })
        print('created user %s' % h['id'])

    elif action == 'update-user-fullname':
        email, name = args[1:]

        h = proxy.User.update({
            'names': [email],
            'full_name': name,
        })
        print('updated user %s' % h['users'][0]['id'])

    elif action == 'update-user-email':
        old_email, new_email = args[1:]

        h = proxy.User.update({
            'names': [old_email],
            'email': new_email,
        })
        print('updated user %s' % h['users'][0]['id'])

    elif action == 'update-user-login-denied-text':
        email, text = args[1:]

        h = proxy.User.update({
            'names': [email],
            'login_denied_text': text,
        })
        print('updated user %s' % h['users'][0]['id'])

    elif action == 'create-group':
        group, desc = args[1:]
        # Adding every user to every group is wrong. This is a quick hack to
        # work around bug 1079463.
        h = proxy.Group.create({
            'name': group,
            'description': desc,
            'user_regexp': '.*',
        })

    elif action == 'create-login-cookie':
        # We simulate a browser's HTML interaction with Bugzilla to obtain a
        # login cookie. Is there a better way?
        url = os.environ['BUGZILLA_URL']
        r = requests.get(url + '/')
        cookies = dict(r.cookies)

        params = {
            'Bugzilla_login': os.environ['BUGZILLA_USERNAME'],
            'Bugzilla_password': os.environ['BUGZILLA_PASSWORD'],
            'Bugzilla_login_token': '',
        }
        r = requests.post(url + '/index.cgi', params=params, cookies=cookies)
        if r.status_code != 200:
            raise Exception('Non-200 response from Bugzilla. Proper credentials?')

        login = r.cookies['Bugzilla_login']
        cookie = r.cookies['Bugzilla_logincookie']
        print('%s %s' % (login, cookie))

    else:
        print('unknown action: %s' % action)
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
