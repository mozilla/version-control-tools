# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import ugettext as _
from djblets.siteconfig.models import SiteConfiguration
from reviewboard.accounts.backends import AuthBackend

from rbbz.bugzilla import Bugzilla
from rbbz.errors import BugzillaAuthError, BugzillaError
from rbbz.forms import BugzillaAuthSettingsForm
from rbbz.models import get_or_create_bugzilla_users


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
        siteconfig = SiteConfiguration.objects.get_current()
        xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not xmlrpc_url:
            return None

        bugzilla = Bugzilla(xmlrpc_url)
        user_data = bugzilla.log_in(username, password, cookie)

        if not user_data:
            return None

        users = get_or_create_bugzilla_users(user_data)

        if not users:
            return None

        user = users[0]

        if not user.is_active:
            return None

        if not cookie:
            (user.bzlogin, user.bzcookie) = bugzilla.cookies()

        return user

    def get_or_create_user(self, username, request):
        """Always check Bugzilla for updates."""
        username = username.strip()
        siteconfig = SiteConfiguration.objects.get_current()
        xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not xmlrpc_url:
            return None

        try:
            bugzilla = Bugzilla(xmlrpc_url, request.session)
        except BugzillaAuthError:
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

        siteconfig = SiteConfiguration.objects.get_current()
        xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not xmlrpc_url:
            return None

        try:
            bugzilla = Bugzilla(xmlrpc_url, request.session)
        except BugzillaAuthError:
            raise PermissionDenied

        try:
            get_or_create_bugzilla_users(bugzilla.query_users(query))
        except BugzillaError:
            raise PermissionDenied

    def search_users(self, query, request):
        """Search anywhere in name to support BMO :irc_nick convention."""
        q = Q(username__icontains=query)

        if request.GET.get('fullname', None):
            q = q | (Q(first_name__icontains=query) |
                     Q(last_name__icontains=query))

        return q
