# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64

import bugsy
import mechanize
import requests
import xmlrpclib
import yaml

from mozreview.bugzilla.transports import bugzilla_transport


def create_xmlrpc_proxy(url, username, password):
    """Obtain an XMLRPC proxy to the Bugzilla service."""
    transport = bugzilla_transport(url)
    proxy = xmlrpclib.ServerProxy(url, transport)
    proxy.User.login({'login': username, 'password': password})

    return transport, proxy


class Bugzilla(object):
    """High-level API to common Bugzilla tasks."""

    def __init__(self, base_url, username, password):
        base_url = base_url.rstrip('/')

        self.base_url = base_url
        self.username = username
        self.password = password

        self.xmlrpc_url = base_url + '/xmlrpc.cgi'
        rest_url = base_url + '/rest'

        transport, proxy = create_xmlrpc_proxy(self.xmlrpc_url, username,
                                               password)
        self.proxy = proxy

        userid, cookie = transport.bugzilla_cookies()
        assert userid
        assert cookie

        client = bugsy.Bugsy(username=username, userid=userid, cookie=cookie,
                             bugzilla_url=rest_url)

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

    def create_user(self, email, password, name, touch=True):
        u = self.proxy.User.create({
            'email': email,
            'password': password,
            'full_name': name,
        })

        # Bugzilla imposes restrictions on users that haven't been active
        # in a while (bug 751862). It doesn't count user creation towards
        # the time period. So, we log in users when they are created to mark
        # them as active.
        if touch:
            # Creating the proxy logs in the user.
            create_xmlrpc_proxy(self.xmlrpc_url, email, password)

        return u

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
        br = mechanize.Browser()
        url = self.base_url + '/'
        br.set_handle_robots(False)
        br.open(url)
        br.select_form(nr=0)
        br.form['Bugzilla_login'] = self.username
        br.form['Bugzilla_password'] = self.password
        resp = br.submit()
        if resp.code != 200:
            raise Exception('Non-200 response from Bugzilla. Proper credentials?')
        # Is there a better way to extract cookies?
        cookies = br._ua_handlers['_cookies'].cookiejar

        login = [c.value for c in cookies if c.name == 'Bugzilla_login']
        assert login, "Bugzilla_login cookie not found"

        cookie = [c.value for c in cookies if c.name == 'Bugzilla_logincookie']
        assert cookie, "Bugzilla_logincookie cookie not found"

        return login[0], cookie[0]

    def serialize_bugs(self, bugs):
        data = {}

        for bug in self.proxy.Bug.get({'ids': bugs})['bugs']:
            bid = str(bug['id'])
            d = dict(
                summary=bug['summary'],
                comments=[],
                product=bug['product'],
                component=bug['component'],
                status=bug['status'],
                resolution=bug['resolution'],
                platform=bug['platform'],
                cc=sorted(bug['cc']),
                blocks=sorted(bug['blocks']),
                depends_on=sorted(bug['depends_on']),
            )
            r = self.client.request('bug/%s/comment' % bid)
            for comment in r['bugs'][bid]['comments']:
                lines = comment['text'].splitlines()
                if len(lines) > 1:
                    ct = lines
                else:
                    ct = comment['text']

                d['comments'].append(dict(
                    author=comment['author'],
                    id=comment['id'],
                    tags=sorted(comment['tags']),
                    text=ct,
                ))

            r = self.client.request('bug/%s/attachment' % bid)
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
