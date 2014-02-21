# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import xmlrpclib

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from djblets.siteconfig.models import SiteConfiguration
from reviewboard.accounts.backends import AuthBackend

from rbbz.forms import BugzillaAuthSettingsForm
from rbbz.models import get_or_create_bugzilla_users
from rbbz.transports import bugzilla_transport


class BugzillaBackend(AuthBackend):
    """
    Authenticate a user via Bugzilla XMLRPC.
    """

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

        transport = bugzilla_transport(xmlrpc_url)
        proxy = xmlrpclib.ServerProxy(xmlrpc_url, transport)

        if cookie:
            # Username and password are actually bugzilla cookies.
            transport.set_bugzilla_cookies(username, password)
            user_id = username
        else:
            transport.remove_bugzilla_cookies()

            try:
                result = proxy.User.login({'login': username,
                                           'password': password})
            except xmlrpclib.Fault:
                return None

            user_id = result['id']

        try:
            user_data = proxy.User.get({'ids': [user_id]})
        except xmlrpclib.Fault:
            return None

        users = get_or_create_bugzilla_users(user_data)

        if not users:
            return None

        user = users[0]

        if not user.is_active:
            return None

        if not cookie:
            (user.bzlogin, user.bzcookie) = transport.bugzilla_cookies()

        return user

    def get_or_create_user(self, username, request):
        """Always check Bugzilla for updates."""
        username = username.strip()
        siteconfig = SiteConfiguration.objects.get_current()
        xmlrpc_url = siteconfig.get('auth_bz_xmlrpc_url')

        if not xmlrpc_url:
            return None

        transport = bugzilla_transport(xmlrpc_url)

        if not transport.set_bugzilla_cookies_from_request(request):
            raise self.bz_error_response(request)

        proxy = xmlrpclib.ServerProxy(xmlrpc_url, transport)

        try:
            user_data = proxy.User.get({'names': [username]})
        except xmlrpclib.Fault:
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

        transport = bugzilla_transport(xmlrpc_url)

        if not transport.set_bugzilla_cookies_from_request(request):
            raise PermissionDenied

        proxy = xmlrpclib.ServerProxy(xmlrpc_url, transport)

        try:
            get_or_create_bugzilla_users(proxy.User.get({'match': [query]}))
        except xmlrpclib.Fault:
            raise PermissionDenied
