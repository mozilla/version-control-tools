# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import xmlrpclib

from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from mozreview.bugzilla.errors import BugzillaError, BugzillaUrlError
from mozreview.bugzilla.transports import bugzilla_transport


@simple_decorator
def xmlrpc_to_bugzilla_errors(func):
    def _transform_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except xmlrpclib.Fault as e:
            if e.faultCode == 307:
                # The Bugzilla error message about expired cookies and tokens
                # is a little confusing in the context of MozReview. Override
                # it with one that makes more sense to users.
                fault_string = ('MozReview\'s Bugzilla session has expired. '
                                'Please log out of Review Board and back in, '
                                'and then retry your action.')
            else:
                fault_string = e.faultString

            raise BugzillaError(fault_string, e.faultCode)
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

    def __init__(self, api_key=None, xmlrpc_url=None):
        self.api_key = api_key
        self._transport = None
        self._proxy = None

        if xmlrpc_url:
            self.xmlrpc_url = xmlrpc_url
        else:
            siteconfig = SiteConfiguration.objects.get_current()
            self.xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not self.xmlrpc_url:
            raise BugzillaUrlError('no XMLRPC URL')

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
        }

        try:
            return self.proxy.User.get(params)
        except xmlrpclib.Fault as e:
            raise

    @xmlrpc_to_bugzilla_errors
    def get_user(self, username):
        params = self._auth_params({
            'names': [username],
            'include_fields': self.user_fields
        })
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def query_users(self, query):
        params = self._auth_params({
            'match': [query],
            'include_fields': self.user_fields
        })
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def get_user_from_userid(self, userid):
        """Convert an integer user ID to string username."""
        params = self._auth_params({
            'ids': [userid],
            'include_fields': self.user_fields
        })
        return self.proxy.User.get(params)

    @xmlrpc_to_bugzilla_errors
    def post_comment(self, bug_id, comment):
        params = self._auth_params({
            'id': bug_id,
            'comment': comment
        })
        return self.proxy.Bug.add_comment(params)

    @xmlrpc_to_bugzilla_errors
    def is_bug_confidential(self, bug_id):
        # We don't need to authenticate here; if we can't get the bug,
        # that itself means it's confidential.
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
        """Creates or updates an attachment containing a review-request URL.

        The reviewers argument should be a dictionary mapping reviewer email
        to a boolean indicating if that reviewer has given an r+ on the
        attachment in the past that should be left untouched.
        """

        # Copy because we modify it.
        reviewers = reviewers.copy()
        params = self._auth_params({})
        flags = []
        rb_attachment = None
        attachments = self.get_rb_attachments(bug_id)

        # Find the associated attachment, then go through the review flags.
        for a in attachments:
            if a['data'] != url:
                continue

            rb_attachment = a

            for f in a.get('flags', []):
                if f['name'] not in ['review', 'feedback']:
                    # We only care about review and feedback flags.
                    continue
                elif f['name'] == 'feedback':
                    # We always clear feedback flags.
                    flags.append({'id': f['id'], 'status': 'X'})
                elif f['status'] == '+' and f['setter'] not in reviewers:
                    # This r+ flag was set manually on bugzilla rather
                    # then through a review on Review Board. Always
                    # clear these flags.
                    flags.append({'id': f['id'], 'status': 'X'})
                elif f['status'] == '+':
                    if not reviewers[f['setter']]:
                        # We should not carry this r+ forward so
                        # re-request review.
                        flags.append({
                            'id': f['id'],
                            'name': 'review',
                            'status': '?',
                            'requestee': f['setter']
                        })

                    reviewers.pop(f['setter'])
                elif 'requestee' not in f or f['requestee'] not in reviewers:
                    # We clear review flags where the requestee is not
                    # a reviewer or someone has manually set r- on the
                    # attachment.
                    flags.append({'id': f['id'], 'status': 'X'})
                elif f['requestee'] in reviewers:
                    # We're already waiting for a review from this user
                    # so don't touch the flag.
                    reviewers.pop(f['requestee'])

            break

        # Add flags for new reviewers.

        # Sorted so behavior is deterministic (this mucks with test output
        # otherwise).
        for r in sorted(reviewers.keys()):
            flags.append({
                'name': 'review',
                'status': '?',
                'requestee': r,
                'new': True
            })

        if rb_attachment:
            params['ids'] = [rb_attachment['id']]

            if rb_attachment['is_obsolete']:
                params['is_obsolete'] = False
        else:
            params['ids'] = [bug_id]
            params['data'] = url
            params['content_type'] = 'text/x-review-board-request'

        params['file_name'] = 'reviewboard-%d-url.txt' % review_id
        params['summary'] = "MozReview Request: %s" % summary
        params['comment'] = comment
        if flags:
            params['flags'] = flags

        if rb_attachment:
            self.proxy.Bug.update_attachment(params)
        else:
            self.proxy.Bug.add_attachment(params)

    @xmlrpc_to_bugzilla_errors
    def get_rb_attachments(self, bug_id):
        """Get all attachments that contain review-request URLs."""

        params = self._auth_params({
            'ids': [bug_id],
            'include_fields': ['id', 'data', 'content_type', 'is_obsolete',
                               'flags']
        })

        return [a for a
                in self.proxy.Bug.attachments(params)['bugs'][str(bug_id)]
                if a['content_type'] == 'text/x-review-board-request']

    def _get_review_request_attachment(self, bug_id, rb_url):
        """Obtain a Bugzilla attachment for a review request."""
        for a in self.get_rb_attachments(bug_id):
            if a.get('data') == rb_url:
                return a

        return None

    @xmlrpc_to_bugzilla_errors
    def r_plus_attachment(self, bug_id, reviewer, rb_url, comment=None):
        """Set a review flag to "+".

        Does nothing if the reviewer has already r+ed the attachment.
        Updates flag if a corresponding r? is found; otherwise creates a
        new flag.

        We return a boolean indicating whether we r+ed the attachment.
        """

        logging.info('r+ from %s on bug %d.' % (reviewer, bug_id))

        rb_attachment = self._get_review_request_attachment(bug_id, rb_url)
        if not rb_attachment:
            logging.error('Could not find attachment for Review Board URL %s '
                          'in bug %s.' % (rb_url, bug_id))
            return False

        flags = rb_attachment.get('flags', [])
        flag = {'name': 'review', 'status': '+'}

        for f in flags:
            if f['name'] == 'review' and f.get('requestee') == reviewer:
                flag['id'] = f['id']
                break
            elif (f['name'] == 'review' and f.get('setter') == reviewer and
                  f['status'] == '+'):
                logging.info('r+ already set.')
                return False
        else:
            flag['new'] = True
            flag['requestee'] = reviewer

        params = self._auth_params({
            'ids': [rb_attachment['id']],
            'flags': [flag],
        })

        if comment:
            params['comment'] = comment

        self.proxy.Bug.update_attachment(params)
        return True

    @xmlrpc_to_bugzilla_errors
    def cancel_review_request(self, bug_id, reviewer, rb_url, comment=None):
        """Cancel an r? or r+ flag on a Bugzilla attachment.

        We return a boolean indicating whether we cancelled a review request.
        This is so callers can do something with the comment (which won't get
        posted unless the review flag was cleared).
        """
        logging.info('maybe cancelling r? from %s on bug %d.' % (reviewer,
                                                                 bug_id))

        rb_attachment = self._get_review_request_attachment(bug_id, rb_url)

        if not rb_attachment:
            return False

        flags = rb_attachment.get('flags', [])
        flag = {'name': 'review', 'status': 'X'}

        for f in flags:
            logging.info("Flag %s" % f)
            if f['name'] == 'review' and (f.get('requestee') == reviewer or
                                          (f.get('setter') == reviewer and
                                           f.get('status') == '+')):
                flag['id'] = f['id']
                break
        else:
            return False

        params = self._auth_params({
            'ids': [rb_attachment['id']],
            'flags': [flag],
        })

        if comment:
            params['comment'] = comment

        self.proxy.Bug.update_attachment(params)
        return True

    @xmlrpc_to_bugzilla_errors
    def obsolete_review_attachments(self, bug_id, rb_url):
        """Mark any attachments for a given bug and review request as obsolete.

        This is called when review requests are discarded or deleted. We don't
        want to leave any lingering references in Bugzilla.
        """
        params = self._auth_params({
            'ids': [],
            'is_obsolete': True,
        })

        for a in self.get_rb_attachments(bug_id):
            if a.get('data') == rb_url and not a.get('is_obsolete'):
                params['ids'].append(a['id'])

        if params['ids']:
            self.proxy.Bug.update_attachment(params)

    @xmlrpc_to_bugzilla_errors
    def valid_api_key(self, username, api_key):
        try:
            return self.proxy.User.valid_login({
                'login': username,
                'api_key': api_key,
            })
        except xmlrpclib.Fault as e:
            # Invalid API-key formats (e.g. not 40 characters long) or expired
            # API keys will raise an error, but for our purposes we just
            # consider them as invalid proper API keys, particularly so we can
            # try another type of authentication.
            if e.faultCode == 306:
                return False

            raise

    def _auth_params(self, params):
        if not self.api_key:
            raise BugzillaError('There is no Bugzilla API key on record for '
                                'this user. Please log into MozReview\'s '
                                'UI to have one generated.')

        params['api_key'] = self.api_key
        return params

    @property
    def transport(self):
        if self._transport is None:
            self._transport = bugzilla_transport(self.xmlrpc_url)

        return self._transport

    @property
    def proxy(self):
        if self._proxy is None:
            self._proxy = xmlrpclib.ServerProxy(self.xmlrpc_url,
                                                self.transport)

        return self._proxy
