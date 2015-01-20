# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from rbbz.auth import BugzillaBackend

from django.conf import settings
from reviewboard.accounts.backends import get_enabled_auth_backends


class BugzillaCookieAuthMiddleware(object):
    """Set Bugzilla login cookies from auth backend."""

    def process_request(self, request):
        if BugzillaBackend not in [x.__class__ for
                                   x in get_enabled_auth_backends()]:
            return

        request.user.bzlogin = request.session.get('Bugzilla_login')
        request.user.bzcookie = request.session.get('Bugzilla_logincookie')

    def process_response(self, request, response):
        if BugzillaBackend not in [x.__class__ for
                                   x in get_enabled_auth_backends()]:
            return response

        if not hasattr(request, 'user'):
            return response

        if not request.user.is_authenticated():
            for key in ('Bugzilla_login', 'Bugzilla_logincookie'):
                try:
                    del request.session[key]
                except KeyError:
                    pass

            return response

        try:
            bzlogin = getattr(request.user, 'bzlogin')
            bzcookie = getattr(request.user, 'bzcookie')
        except AttributeError:
            return response

        if not bzlogin or not bzcookie:
            return response

        request.session['Bugzilla_login'] = bzlogin
        request.session['Bugzilla_logincookie'] = bzcookie
        return response


class CorsHeaderMiddleware(object):
    """Add a CORS header if running in debug mode."""

    def process_response(self, request, response):
        if settings.DEBUG:
            response['Access-Control-Allow-Origin'] = '*'
        return response
