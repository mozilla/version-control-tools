# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import ugettext as _
from reviewboard.accounts.backends import AuthBackend
from reviewboard.accounts.errors import UserQueryError

from mozreview.models import get_or_create_bugzilla_users
from rbbz.bugzilla import Bugzilla
from rbbz.errors import BugzillaError, BugzillaUrlError
from rbbz.forms import BugzillaAuthSettingsForm


class BugzillaBackend(AuthBackend):
    """
    Authenticate a user via Bugzilla XMLRPC.
    """

    backend_id = _('bugzilla')
    name = _('Bugzilla')
    login_instructions = _('using your Bugzilla credentials.')
    settings_form = BugzillaAuthSettingsForm

    def bz_error_response(self, request):
        logout(request)
        return PermissionDenied

    def authenticate(self, username, password, cookie=False):
        username = username.strip()

        # If the user provides an email address when authenticating,
        # it is checked against Review Board's email field in the User
        # Model.  If a match is found, the email will be translated into
        # the username field before being passed into this method's
        # 'username' argument.
        #
        # If a match is not found, 'username' will contain whatever was
        # entered, which may be the Bugzilla login (email address) for a
        # user who does not yet have an entry in the Review Board
        # database.

        if not cookie:
            try:
                username = User.objects.get(username=username).email
            except User.DoesNotExist:
                pass

        # There is a *tiny* probability that this will not work, but only if
        # user A changes their email address, then user B changes their email
        # address to user A's old email, and Review Board doesn't pick up
        # user A's change because they aren't currently involved in any
        # Review Board reviews.  In this case 'username' would have resolved
        # to user A's address.  There's no easy way to detect this without
        # a search on Bugzilla before every log in, and I (mcote) don't think
        # that's worth it for such an improbable event.
        #
        # This also applies to changes to the user's username, since it has
        # to be unique (see get_or_create_bugzilla_users()).

        try:
            bugzilla = Bugzilla()
        except BugzillaUrlError:
            logging.warn('Login failure for user %s: Bugzilla URL not set.'
                         % username)
            return None

        try:
            user_data = bugzilla.log_in(username, password, cookie)
        except BugzillaError as e:
            logging.error('Login failure for user %s: %s' % (username, e))
            return None

        if not user_data:
            return None

        users = get_or_create_bugzilla_users(user_data)

        if not users:
            logging.error('Login failure for user %s: failed to create user.'
                          % username)
            return None

        user = users[0]

        if not user.is_active:
            logging.error('Login failure for user %s: user is not active.'
                          % username)
            return None

        if not cookie:
            (user.bzlogin, user.bzcookie) = bugzilla.cookies()

        return user

    def get_or_create_user(self, username, request):
        """Always check Bugzilla for updates."""
        username = username.strip()

        try:
            bugzilla = Bugzilla(*self._session_cookies(request.session))
        except BugzillaUrlError:
            return None
        except BugzillaError:
            raise PermissionDenied

        user_data = bugzilla.get_user(username)

        if not user_data:
            raise self.bz_error_response(request)

        # Just store the results.
        get_or_create_bugzilla_users(user_data)

        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    def query_users(self, query, request):
        if not query:
            return

        try:
            bugzilla = Bugzilla(*self._session_cookies(request.session))
        except BugzillaError as e:
            raise UserQueryError('Bugzilla error: %s' % e.msg)

        try:
            get_or_create_bugzilla_users(bugzilla.query_users(query))
        except BugzillaError as e:
            raise UserQueryError('Bugzilla error: %s' % e.msg)

    def search_users(self, query, request):
        """Search anywhere in name to support BMO :irc_nick convention."""
        q = Q(username__icontains=query)
        q = q | Q(email__icontains=query)

        if request.GET.get('fullname', None):
            q = q | (Q(first_name__icontains=query) |
                     Q(last_name__icontains=query))

        return q

    def _session_cookies(self, session):
        return (session.get('Bugzilla_login'),
                session.get('Bugzilla_logincookie'))
