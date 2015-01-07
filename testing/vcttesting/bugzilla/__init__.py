# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64

import bugsy
import requests
import xmlrpclib
import yaml

from rbbz.transports import bugzilla_transport

class Bugzilla(object):
    """High-level API to common Bugzilla tasks."""

    def __init__(self, base_url, username, password):
        base_url = base_url.rstrip('/')

        self.base_url = base_url
        self.username = username
        self.password = password

        xmlrpc_url = base_url + '/xmlrpc.cgi'
        rest_url = base_url + '/rest'

        transport = bugzilla_transport(xmlrpc_url)
        proxy = xmlrpclib.ServerProxy(xmlrpc_url, transport)
        proxy.User.login({'login': username, 'password': password})

        client = bugsy.Bugsy(username=username, password=password,
            bugzilla_url=rest_url)

        self.proxy = proxy
        self.client = client

    def create_bug(self, product, component, summary):
        bug = bugsy.Bug(self.client, product=product, component=component,
                summary=summary)
        self.client.put(bug)

    def create_bug_range(self, product, component, total):
        first = None
        last = None
        for i in range(0, total):
            bug = bugsy.Bug(self.client, product=product, component=component,
                    summary='Range %d' % (i + 1))
            self.client.put(bug)

            if i == 0:
                first = bug.id
            else:
                last = bug.id

        return total, first, last

    def create_group(self, group, description):
        # Adding every user to every group is wrong. This is a quick hack to
        # work around bug 1079463.
        return self.proxy.Group.create({
            'name': group,
            'description': description,
            'user_regexp': '.*',
        })

    def create_user(self, email, password, name):
        return self.proxy.User.create({
            'email': email,
            'password': password,
            'full_name': name,
        })

    def add_user_to_group(self, email, group):
        return self.proxy.User.update({
            'names': [email],
            'groups': {'add': [group]},
            })

    def update_user_fullname(self, email, name):
        return self.proxy.User.update({
            'names': [email],
            'full_name': name,
        })

    def update_user_email(self, old_email, new_email):
        return self.proxy.User.update({
            'names': [old_email],
            'email': new_email,
        })

    def update_user_login_denied_text(self, email, text):
        return self.proxy.User.update({
            'names': [email],
            'login_denied_text': text,
        })

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

        return login, cookie

    def serialize_bugs(self, bugs):
        data = {}
        for bid in bugs:
            bug = self.client.get(bid)

            d = dict(
                summary=bug.summary,
                comments=[],
                product=bug.product,
                component=bug.component,
                status=bug.status,
                resolution=bug.resolution,
                platform=bug.platform,
            )
            for comment in bug.get_comments():
                d['comments'].append(dict(
                    author=comment.author,
                    id=comment.id,
                    tags=sorted(comment.tags),
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
                    file_name=a['file_name'],
                    attacher=a['attacher'],
                    content_type=a['content_type'],
                    description=a['description'],
                    summary=a['summary'],
                    data=base64.b64decode(a['data']),
                    flags=flags,
                    is_obsolete=bool(a['is_obsolete']),
                    is_patch=bool(a['is_patch'])))

            key = 'Bug %s' % bid
            data[key] = d

        return yaml.safe_dump(data, default_flow_style=False).rstrip()
