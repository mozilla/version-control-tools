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
        'dump-bug',
        'update-user-login-denied-text',
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

    if action == 'dump-bug':
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

    elif action == 'update-user-login-denied-text':
        email, text = args[1:]

        h = proxy.User.update({
            'names': [email],
            'login_denied_text': text,
        })
        print('updated user %s' % h['users'][0]['id'])

    else:
        print('unknown action: %s' % action)
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
