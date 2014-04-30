# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import xmlrpclib

from djblets.siteconfig.models import SiteConfiguration

from rbbz.errors import BugzillaError, BugzillaUrlError
from rbbz.transports import bugzilla_transport


class Bugzilla(object):
    """
    Interface to a Bugzilla system.

    At the moment this uses the XMLRPC API.  It should probably be converted
    to REST at some point.

    General FIXME: try to get more specific errors out of xmlrpclib.Fault
    exceptions.
    """

    def __init__(self, login=None, logincookie=None):
        siteconfig = SiteConfiguration.objects.get_current()
        self.xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not self.xmlrpc_url:
            raise BugzillaUrlError('no XMLRPC URL')

        self._transport = None
        self._proxy = None

        if logincookie:
            self.transport.set_bugzilla_cookies(login, logincookie)

    def cookies(self):
        return self.transport.bugzilla_cookies()

    def log_in(self, username, password, cookie=False):
        if cookie:
            # Username and password are actually bugzilla cookies.
            self.transport.set_bugzilla_cookies(username, password)
            user_id = username
        else:
            self.transport.remove_bugzilla_cookies()

            try:
                result = self.proxy.User.login({'login': username,
                                                'password': password})

            except xmlrpclib.Fault as e:
                if e.faultCode == 300 or e.faultCode == 301:
                    # Invalid username/password or account disabled
                    return None
                raise BugzillaError(e.faultString)

            user_id = result['id']

        params = {'ids': [user_id],
                  'include_fields': ['email', 'real_name', 'can_login']}

        try:
            return self.proxy.User.get(params)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)

    def get_user(self, username):
        params = {'names': [username],
                  'include_fields': ['email', 'real_name', 'can_login']}

        try:
            return self.proxy.User.get(params)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)

    def query_users(self, query):
        params = {'match': [query],
                  'include_fields': ['email', 'real_name', 'can_login']}

        try:
            return self.proxy.User.get(params)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)

    def post_comment(self, bug_id, comment):
        params = {
            'id': bug_id,
            'comment': comment
        }

        try:
            return self.proxy.Bug.add_comment(params)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)

    def post_rb_url(self, summary, bug_id, url, reviewer):
        params = {
            'ids': [bug_id],
            'data': url,
            'file_name': summary,
            'summary': summary,
            'content_type': 'text/plain',
            'flags': [{'name': 'review',
                       'status': '?',
                       'requestee': reviewer}]
        }

        try:
            return self.proxy.Bug.add_attachment(params)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)

    @property
    def transport(self):
        if self._transport is None:
            self._transport = bugzilla_transport(self.xmlrpc_url)

        return self._transport

    @property
    def proxy(self):
        if self._proxy is None:
            self._proxy = xmlrpclib.ServerProxy(self.xmlrpc_url, self.transport)

        return self._proxy
