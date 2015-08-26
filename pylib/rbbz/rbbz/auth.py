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

from mozreview.bugzilla.client import Bugzilla
from mozreview.bugzilla.errors import BugzillaError, BugzillaUrlError
from mozreview.bugzilla.models import (
    BugzillaUserMap,
    BZ_IRCNICK_RE,
    get_bugzilla_api_key,
    get_or_create_bugzilla_users,
)
from mozreview.errors import (
    BugzillaAPIKeyNeededError,
    WebLoginNeededError,
)
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

        return user

    def authenticate_api_key(self, username, api_key):
        """Authenticate a user from a username and API key.

        This is intended to be used by the Web API and not a user-facing
        login form. We enforce that the user already exists and has an
        API key - not necessarily the same API key - on file. The API key
        passed in is only used for authentication: all subsequent communication
        with Bugzilla should be performed using the API key on file.

        We require the user already exist in the database because having
        the user go through the browser-facing login flow is the most sane
        (and secure) way to obtain an API key. We don't want to store the
        API key provided to us from the client because API keys obtained by
        the browser login may have special permissions not granted to normal
        API keys.
        """
        username = username.strip()

        try:
            bugzilla = Bugzilla()
        except BugzillaUrlError:
            logging.warn('Login failure for user %s: Bugzilla URL not set.' %
                         username)

        try:
            valid = bugzilla.valid_api_key(username, api_key)
        except BugzillaError as e:
            logging.error('Login failure for user %s: %s' % (username, e))
            return None

        if not valid:
            logging.error('Login failure for user %s: invalid API key' %
                          username)
            assert bugzilla.base_url.endswith('/')
            raise BugzillaAPIKeyNeededError(
                    bugzilla.base_url + 'userprefs.cgi?tab=apikey')

        # Assign the API key to the Bugzilla connection so the user info
        # lookup uses it.
        # TODO can we skip valid_api_key() and just get user info straight up?
        bugzilla.api_key = api_key

        try:
            user_data = bugzilla.get_user(username)
        except BugzillaError as e:
            logging.error('Login failure for user %s: unable to retrieve '
                          'Bugzilla user info: %s' % (username, e))
            return None

        if not user_data:
            logging.warning('Could not retrieve user info for %s after '
                            'validating API key' % username)
            return None

        bz_user = user_data['users'][0]

        try:
            bum = BugzillaUserMap.get(bugzilla_user_id=bz_user['id'])
            user = bum.user
        except BugzillaUserMap.DoesNotExist:
            logging.warning('Login failure for user %s: API key valid but '
                            'user missing from database' % username)
            raise WebLoginNeededError()

        if not user.is_active:
            logging.error('Login failure for user %s: user not active' %
                          username)
            return None

        # We require a local API key to be on file, as it will be used for
        # subsequent requests.
        if not get_bugzilla_api_key(user):
            logging.warning('Login failure for user %s: no API key in '
                            'database' % username)
            raise WebLoginNeededError()

        return user

    def get_or_create_user(self, username, request):
        """Always check Bugzilla for updates."""
        username = username.strip()

        try:
            bugzilla = Bugzilla(get_bugzilla_api_key(request.user))
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
            bugzilla = Bugzilla(get_bugzilla_api_key(request.user))
        except BugzillaError as e:
            raise UserQueryError('Bugzilla error: %s' % e.msg)

        try:
            # We don't want to auto populate just any user because Bugzilla has
            # over 300,000 users and most of them aren't relevant to MozReview.
            #
            # So, we only auto import users if they have IRC nick syntax or
            # if the search matches them exactly.
            def user_relevant(u):
                if BZ_IRCNICK_RE.search(u['real_name']):
                    return True
                if u['email'] == query:
                    return True

                # This might allow too many users through. Let's not get too
                # attached to this.
                if u['real_name'] == query:
                    return True

                return False

            users = bugzilla.query_users(query)
            users['users'] = [u for u in users['users'] if user_relevant(u)]
            get_or_create_bugzilla_users(users)
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
