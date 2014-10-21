# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import xmlrpclib

from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from rbbz.errors import BugzillaError, BugzillaUrlError
from rbbz.transports import bugzilla_transport


@simple_decorator
def xmlrpc_to_bugzilla_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpclib.Fault as e:
            raise BugzillaError(e.faultString, e.faultCode)
        except xmlrpclib.ProtocolError as e:
            raise BugzillaError('ProtocolError: %s' % e.errmsg, e.errcode)
        except IOError as e:
            # Raised when the protocol is invalid or the server can't be
            # found.
            msg = 'unknown'

            if e.args:
                msg = e.args[0]

            raise BugzillaError('IOError: %s' % msg)
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
    AUTHORIZED_GROUP = 'reviewboard'

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
                if e.faultCode == 300:
                    logging.error('Login failure for user %s: '
                                  'invalid username or password.' % username)
                    return None
                elif e.faultCode == 301:
                    logging.error('Login failure for user %s: '
                                  'user is disabled.' % username)
                    return None
                raise

            user_id = result['id']

        params = {
            'ids': [user_id],
            'include_fields': self.user_fields,
            'groups': [self.AUTHORIZED_GROUP]
        }

        try:
            return self.proxy.User.get(params)
        except xmlrpclib.Fault as e:
            if e.faultCode == 804:
                logging.error('Login failure for user %s: user is not part '
                              'of the "%s" group.' %
                              (username, self.AUTHORIZED_GROUP))
                return None
            raise

    @xmlrpc_to_bugzilla_errors
    def get_user(self, username):
        params = {'names': [username], 'include_fields': self.user_fields}
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def query_users(self, query):
        params = {'match': [query], 'include_fields': self.user_fields}
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def get_user_from_userid(self, userid):
        """Convert an integer user ID to string username."""
        params = {'ids': [userid], 'include_fields': self.user_fields}
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
    def post_rb_url(self, bug_id, review_id, summary, comment, url,
                    reviewers):
        """Posts a new attachment containing a review-request URL, or updates
           an existing one."""

        reviewers = set(reviewers)
        params = {}
        flags = []
        rb_attachment = None
        attachments = self.get_rb_attachments(bug_id)

        # Find the associated attachment, then go through the review flags.
        # If a review flag status is '?' and the requestee is still in the
        # given reviewers, then update the flag.
        # If the review flag status is other than '?', or if it is a feedback
        # flag, clear it.

        for a in attachments:
            if a['data'] != url:
                continue

            rb_attachment = a

            for f in a.get('flags', []):
                if f['name'] != 'review' and f['name'] != 'feedback':
                    continue

                if (f['name'] == 'review' and 'requestee' in f
                    and f['requestee'] in reviewers):
                    flags.append({'id': f['id'], 'name': 'review',
                                  'status': '?',
                                  'requestee': f['requestee']})
                    reviewers.remove(f['requestee'])
                else:
                    flags.append({'id': f['id'], 'status': 'X'})

            break

        # Add flags for new reviewers.

        for r in reviewers:
            flags.append({'name': 'review', 'status': '?', 'requestee': r,
                          'new': True})

        if rb_attachment:
            params['ids'] = [rb_attachment['id']]
        else:
            params['ids'] = [bug_id]
            params['data'] = url
            params['content_type'] = 'text/x-review-board-request'

        params['file_name'] = 'reviewboard-%d-url.txt' % review_id
        params['summary'] = "MozReview Request: %s" % summary
        if flags:
            params['flags'] = flags

        if rb_attachment:
            self.proxy.Bug.update_attachment(params)
        else:
            self.proxy.Bug.add_attachment(params)

        # FIXME: The comment should be posted as part of add/update_attachment,
        # but due to bug 508541, the comment won't be included in the bugmail,
        # so until that bug is fixed, we sent the comment separately, after
        # setting the flag.
        self.post_comment(bug_id, comment)


    @xmlrpc_to_bugzilla_errors
    def get_rb_attachments(self, bug_id):
        """Get all attachments that contain review-request URLs."""

        params = {
            'ids': [bug_id],
            'include_fields': ['id', 'data', 'content_type', 'is_obsolete',
                               'flags']
        }

        return [a for a
                in self.proxy.Bug.attachments(params)['bugs'][str(bug_id)]
                if not a['is_obsolete'] and
                a['content_type'] == 'text/x-review-board-request']

    @xmlrpc_to_bugzilla_errors
    def r_plus_attachment(self, bug_id, reviewer, comment, rb_url):
        """Set a review flag to "+"."""

        logging.info('r+ from %s on bug %d.' % (reviewer, bug_id))

        rb_attachment = None
        attachments = self.get_rb_attachments(bug_id)

        for a in attachments:
            if a.get('data') == rb_url:
                rb_attachment = a
                break

        if not rb_attachment:
            return

        flags = rb_attachment.get('flags', [])
        new_flag = {'name': 'review', 'status': '+'}

        for f in flags:
            if f['name'] == 'review' and f.get('requestee') == reviewer:
                new_flag['id'] = f['id']
                break
        else:
            new_flag['new'] = True
            new_flag['requestee'] = reviewer

        params = {
            'ids': [rb_attachment['id']],
            'flags': [new_flag]
        }

        self.proxy.Bug.update_attachment(params)
        # FIXME: The comment should be posted as part of update_attachment,
        # but due to bug 508541, the comment won't be included in the bugmail,
        # so until that bug is fixed, we sent the comment separately, after
        # setting the flag.
        self.post_comment(bug_id, comment)


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
