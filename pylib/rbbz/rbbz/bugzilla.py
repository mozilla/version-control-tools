# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import xmlrpclib

from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from rbbz.errors import BugzillaError, BugzillaUrlError
from rbbz.transports import bugzilla_transport


ATTACHMENT_SUMMARY_PREFIX = '[RB] '

@simple_decorator
def xmlrpc_to_bugzilla_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString)
    return _transform_errors


class Bugzilla(object):
    """
    Interface to a Bugzilla system.

    At the moment this uses the XMLRPC API.  It should probably be converted
    to REST at some point.

    General FIXME: try to get more specific errors out of xmlrpclib.Fault
    exceptions.
    """

    user_fields = ['id', 'email', 'real_name', 'can_login']

    def __init__(self, login=None, logincookie=None, xmlrpc_url=None):
        if xmlrpc_url:
            self.xmlrpc_url = xmlrpc_url
        else:
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

    @xmlrpc_to_bugzilla_errors
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
                raise

            user_id = result['id']

        params = {'ids': [user_id], 'include_fields': self.user_fields}

        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def get_user(self, username):
        params = {'names': [username], 'include_fields': self.user_fields}
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def query_users(self, query):
        params = {'match': [query], 'include_fields': self.user_fields}
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def post_comment(self, bug_id, comment):
        params = {
            'id': bug_id,
            'comment': comment
        }
        return self.proxy.Bug.add_comment(params)

    @xmlrpc_to_bugzilla_errors
    def is_bug_confidential(self, bug_id):
        params = {'ids': [bug_id], 'include_fields': ['groups']}

        try:
            groups = self.proxy.Bug.get(params)['bugs'][0]['groups']
        except xmlrpclib.Fault as e:
            if e.faultCode == 102:
                return True
            raise

        return bool(groups)

    @xmlrpc_to_bugzilla_errors
    def post_rb_url(self, summary, bug_id, url, reviewer):
        params = {
            'ids': [bug_id],
            'data': url,
            'file_name': summary,
            'summary': '%s%s' % (ATTACHMENT_SUMMARY_PREFIX, summary),
            'content_type': 'text/plain',
            'flags': [{'name': 'review',
                       'status': '?',
                       'requestee': reviewer}]
        }
        return self.proxy.Bug.add_attachment(params)

    @xmlrpc_to_bugzilla_errors
    def get_rb_attachments(self, bug_id):
        rb_attachments = []
        params = {
            'ids': [bug_id],
            'include_fields': ['id', 'data', 'summary', 'is_obsolete',
                               'flags']
        }
        attachments = self.proxy.Bug.attachments(params)

        for a in attachments['bugs'][str(bug_id)]:
            if (a['is_obsolete']
                or not a['summary'].startswith(ATTACHMENT_SUMMARY_PREFIX)
                or not a['flags']):
                continue

            reviewer = None

            for f in a['flags']:
                if f['name'] == 'review' and 'requestee' in f:
                    reviewer = f['requestee']
                    break

            if not reviewer:
                continue

            rb_attachments.append({
                    'id': a['id'],
                    'url': a['data'].data,
                    'reviewer': reviewer
            })

        return rb_attachments

    @xmlrpc_to_bugzilla_errors
    def r_plus_attachment(self, attachment_id):
        params = {
            'ids': [attachment_id],
            'flags': [{'name': 'review', 'status': '+'}]
        }

        self.proxy.Bug.update_attachment(params)

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
