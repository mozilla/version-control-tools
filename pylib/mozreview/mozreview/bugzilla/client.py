# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import posixpath
import xmlrpclib

from urlparse import urlparse, urlunparse

from django.contrib.auth.models import User
from djblets.siteconfig.models import SiteConfiguration
from djblets.util.decorators import simple_decorator

from mozautomation.bugzilla_transports import bugzilla_transport
from mozreview.bugzilla.errors import BugzillaError, BugzillaUrlError
from mozreview.bugzilla.models import get_or_create_bugzilla_users
from mozreview.rb_utils import (
    get_diff_url,
    get_diff_url_from_rr_url,
    get_obj_url,
)

from mozautomation.commitparser import (
    replace_reviewers,
    strip_commit_metadata,
)


logger = logging.getLogger(__name__)


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


class BugzillaAttachmentUpdates(object):
    """Create and update attachments.

    This class provides methods to queue up a series of operations on one
    or more attachments and then execute them all together.  It caches
    attachment information to avoid repeatedly polling Bugzilla.

    All attachments to be created or updated must belong to the same bug.
    """

    def __init__(self, bugzilla, bug_id):
        self.bugzilla = bugzilla
        self.bug_id = bug_id
        self.attachments = []
        self.updates = []
        self.creates = []

    def create_or_update_attachment(self, review_request, review_request_draft,
                                    flags):
        """Create or update the MozReview attachment using the provided flags.

        The `flags` parameter is an array of flags to set/update/clear.  This
        array matches the Bugzilla flag API:
        Setting:
            {
                'id': flag.id
                'name': 'review',
                'status': '?',
                'requestee': reviewer.email
            }
        Clearing:
            {
                'id': flag.id,
                'status': 'X'
            }
        """

        logger.info('Posting review request %s to bug %d.' %
                    (review_request.id, self.bug_id))

        rr_url = get_obj_url(review_request)
        diff_url = get_diff_url(review_request)

        # Build the comment.  Only post a comment if the diffset has
        # actually changed.
        comment = ''
        if review_request_draft.get_latest_diffset():
            diffset_count = review_request.diffset_history.diffsets.count()
            if diffset_count < 1:
                # We don't need the first line, since it is also the attachment
                # summary, which is displayed in the comment.
                full_commit_msg = review_request_draft.description.partition(
                    '\n')[2].strip()

                full_commit_msg = strip_commit_metadata(full_commit_msg)

                if full_commit_msg:
                    full_commit_msg += '\n\n'

                comment = '%sReview commit: %s\nSee other reviews: %s' % (
                    full_commit_msg,
                    diff_url,
                    rr_url
                )
            else:
                comment = ('Review request updated; see interdiff: '
                           '%sdiff/%d-%d/\n' % (rr_url,
                                                diffset_count,
                                                diffset_count + 1))

        # Set up attachment metadata.
        attachment = self.get_attachment(review_request)
        params = {}
        if attachment:
            params['attachment_id'] = attachment['id']

            if attachment['is_obsolete']:
                params['is_obsolete'] = False
        else:
            params['data'] = diff_url
            params['content_type'] = 'text/x-review-board-request'

        params['file_name'] = 'reviewboard-%d-url.txt' % review_request.id
        params['summary'] = replace_reviewers(review_request_draft.summary,
                                              None)
        params['comment'] = comment
        if flags:
            params['flags'] = flags

        if attachment:
            self.updates.append(params)
        else:
            self.creates.append(params)

    def obsolete_review_attachments(self, rb_url):
        """Mark any attachments for a given bug and review request as obsolete.

        This is called when review requests are discarded or deleted. We don't
        want to leave any lingering references in Bugzilla.
        """
        self._update_attachments()

        for a in self.attachments:
            if (self.bugzilla._rb_attach_url_matches(a.get('data'), rb_url) and
                    not a.get('is_obsolete')):
                logger.info('Obsoleting attachment %s on bug %d:' % (
                            a['id'], self.bug_id))
                self.updates.append({
                    'attachment_id': a['id'],
                    'is_obsolete': True
                })

    @xmlrpc_to_bugzilla_errors
    def do_updates(self):
        logger.info('Doing attachment updates for bug %s' % self.bug_id)
        params = self.bugzilla._auth_params({
            'bug_id': self.bug_id,
            'attachments': self.creates + self.updates,
            'comment_tags': [self.bugzilla.review_request_comment_tag],
        })

        results = self.bugzilla.proxy.MozReview.attachments(params)

        # The above Bugzilla call is wrapped in a single database transaction
        # and should thus either succeed in creating and updating all
        # attachments or will throw an exception and roll back all changes.
        # However, just to be sure, we check the results.  There's not much
        # we can do in this case, but we'll log an error for investigative
        # purposes.
        # TODO: Display an error in the UI (no easy way to do this without
        # failing the publish).

        ids_to_update = set(u['attachment_id'] for u in self.updates)
        ids_to_update.difference_update(results['attachments_modified'].keys())

        if ids_to_update:
            logger.error('Failed to update the following attachments: %s' %
                         ids_to_update)

        num_to_create = len(self.creates)
        num_created = len(results['attachments_created'])

        if num_to_create != num_created:
            logger.error('Tried to create %s attachments but %s reported as '
                         'created.' % (num_to_create, num_created))

        self.creates = []
        self.updates = []

    def get_attachment(self, review_request):
        """Return the attachment for the specified review request.

        Returns `None` if an attachment hasn't yet been created for the
        review request.
        """
        self._update_attachments()
        url = get_diff_url(review_request)

        for a in self.attachments:
            # Make sure we check for old-style URLs as well.
            if not self.bugzilla._rb_attach_url_matches(a['data'], url):
                continue

            return a

        return None

    def _update_attachments(self):
        if not self.attachments:
            self.attachments = self.bugzilla.get_rb_attachments(self.bug_id)


class Bugzilla(object):
    """
    Interface to a Bugzilla system.

    At the moment this uses the XMLRPC API.  It should probably be converted
    to REST at some point.

    General FIXME: try to get more specific errors out of xmlrpclib.Fault
    exceptions.
    """

    user_fields = ['id', 'email', 'real_name', 'can_login']
    review_request_comment_tag = 'mozreview-request'
    review_comment_tag = 'mozreview-review'
    review_reply_comment_tag = 'mozreview-review-reply'

    def __init__(self, api_key=None, xmlrpc_url=None):
        self.api_key = api_key
        self._transport = None
        self._proxy = None

        siteconfig = SiteConfiguration.objects.get_current()

        if xmlrpc_url:
            self.xmlrpc_url = xmlrpc_url
        else:
            self.xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not self.xmlrpc_url:
            raise BugzillaUrlError('no XMLRPC URL')

        # We only store the xmlrpc URL currently. We should eventually store
        # the Bugzilla base URL and derive the XMLRPC URL from it.
        u = urlparse(self.xmlrpc_url)
        root = posixpath.dirname(u.path).rstrip('/') + '/'
        self.base_url = urlunparse((u.scheme, u.netloc, root, '', '', ''))

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
                    logger.error('Login failure for user %s: '
                                 'invalid username or password.' % username)
                    return None
                elif e.faultCode == 301:
                    logger.error('Login failure for user %s: '
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
    def get_user_from_irc_nick(self, irc_nick):
        irc_nick = irc_nick.lstrip(":").lower()
        users = get_or_create_bugzilla_users(self.query_users(":" + irc_nick))
        for user in users:
            if user.username.lower() == irc_nick:
                return user
        raise User.DoesNotExist()

    @xmlrpc_to_bugzilla_errors
    def post_review_comment(self, bug_id, comment, rb_url, reply=False):
        """Post a comment to a bug representing a review.

        'rb_url' is required so that we can use the MozReview.attachments()
        API, which allows mozreview-* tags to be added to comments even if
        the current user does not belong to the editbugs group.

        'reply' indicates whether this is a reply to a review (True) or just
        a review (False).
        """
        rb_attachment = self._get_review_request_attachment(bug_id, rb_url)

        if not rb_attachment:
            logger.error('Could not find attachment for Review Board URL %s '
                         'in bug %s in order to post comment.'
                         % (rb_url, bug_id))
            return None

        params = self._auth_params({
            'bug_id': bug_id,
            'attachments': [{
                'attachment_id': rb_attachment['id'],
                'comment': comment,
            }],
            'comment_tags': [self.review_reply_comment_tag if reply
                             else self.review_comment_tag],
        })

        logger.info('Posting review comment on bug %d.' % bug_id)
        return self.proxy.MozReview.attachments(params)

    @xmlrpc_to_bugzilla_errors
    def post_comment(self, bug_id, comment):
        """Post a general comment to a bug."""
        params = self._auth_params({
            'id': bug_id,
            'comment': comment,
        })

        logger.info('Posting comment on bug %d.' % bug_id)
        return self.proxy.Bug.add_comment(params)

    @xmlrpc_to_bugzilla_errors
    def is_bug_confidential(self, bug_id):
        # We don't need to authenticate here; if we can't get the bug,
        # that itself means it's confidential.
        params = {'ids': [bug_id], 'include_fields': ['groups']}

        logger.info('Checking if bug %d is confidential.' % bug_id)
        try:
            groups = self.proxy.Bug.get(params)['bugs'][0]['groups']
        except xmlrpclib.Fault as e:
            if e.faultCode == 102:
                logger.info('Bug %d is confidential.' % bug_id)
                return True
            raise

        logger.info('Bug %d confidential: %s.' % (bug_id, bool(groups)))
        return bool(groups)

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

    def _rb_attach_url_matches(self, attach_url, rb_url):
        # Make sure we check for old-style URLs as well.
        return (attach_url == rb_url or
                get_diff_url_from_rr_url(attach_url) == rb_url)

    def _get_review_request_attachment(self, bug_id, rb_url):
        """Obtain a Bugzilla attachment for a review request."""
        for a in self.get_rb_attachments(bug_id):
            if self._rb_attach_url_matches(a.get('data'), rb_url):
                return a

        return None

    @xmlrpc_to_bugzilla_errors
    def set_review_flag(self, bug_id, flag, reviewer, rb_url, comment=None):
        """Create, update or clear a review flag.

        Does nothing if the reviewer has already set the given review flag
        on the attachment.

        Returns a boolean indicating whether we added/cleared a review flag
        on the attachment or not.
        """

        logger.info('%s from %s on bug %d.' % (flag or 'Clearing flag',
                                               reviewer, bug_id))

        flag = flag.strip()

        allowed_flags = {
            'r+': '+',
            'r?': '?',
            'r-': '-',
            '': 'X'
        }
        if flag not in allowed_flags:
            logger.error('Flag change not allowed, flag must be one of '
                         '%s.' % str(allowed_flags))
            return False

        # Convert the flag to its bugzilla-friendly version.
        flag = allowed_flags[flag]

        rb_attachment = self._get_review_request_attachment(bug_id, rb_url)
        if not rb_attachment:
            logger.error('Could not find attachment for Review Board URL %s '
                         'in bug %s.' % (rb_url, bug_id))
            return False

        flag_list = rb_attachment.get('flags', [])
        flag_obj = {'name': 'review', 'status': flag}

        # Only keep review flags.
        review_flags = [f for f in flag_list if f['name'] == 'review']

        for f in review_flags:
            # Bugzilla attachments have a requestee only if the status is `?`.
            # In the other cases requestee == setter.
            if ((reviewer == f.get('requestee') and f['status'] == '?') or
                    (reviewer == f.get('setter') and f['status'] != '?')):

                # Flag is already set, don't change it.
                if f['status'] == flag:
                    logger.info('r%s already set.' % flag)
                    return False

                flag_obj['id'] = f['id']
                break
        else:
            # The reviewer did not have a flag on the attachment.
            if flag == 'X':
                # This shouldn't happen under normal circumstances, but if it
                # does log it.
                logger.info('No flag to clear for %s on %s' % (
                    reviewer, rb_attachment
                ))
                return False

            # Flag not found, let's create a new one.
            flag_obj['new'] = True

        # If the reviewer is setting the flag back to ?,
        # they will then be both the setter and the requestee
        if flag == '?':
            flag_obj['requestee'] = reviewer

        logging.info('sending flag: %s' % flag_obj)

        params = self._auth_params({
            'bug_id': bug_id,
            'attachments': [{
                'attachment_id': rb_attachment['id'],
                'flags': [flag_obj],
            }],
            'comment_tags': ['mozreview-review'],
        })

        if comment:
            params['attachments'][0]['comment'] = comment

        self.proxy.MozReview.attachments(params)
        return True

    @xmlrpc_to_bugzilla_errors
    def r_plus_attachment(self, bug_id, reviewer, rb_url, comment=None):
        """Set a review flag to "+".

        Does nothing if the reviewer has already r+ed the attachment.
        Updates flag if a corresponding r? is found; otherwise creates a
        new flag.

        We return a boolean indicating whether we r+ed the attachment.
        """

        return self.set_review_flag(bug_id, 'r+', reviewer, rb_url, comment)

    @xmlrpc_to_bugzilla_errors
    def cancel_review_request(self, bug_id, reviewer, rb_url, comment=None):
        """Cancel an r? or r+ flag on a Bugzilla attachment.

        We return a boolean indicating whether we cancelled a review request.
        This is so callers can do something with the comment (which won't get
        posted unless the review flag was cleared).
        """
        logger.info('maybe cancelling r? from %s on bug %d.' % (reviewer,
                                                                bug_id))
        return self.set_review_flag(bug_id, '', reviewer, rb_url, comment)

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
