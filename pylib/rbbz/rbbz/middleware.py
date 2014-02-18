# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

class BugzillaCookieAuthMiddleware(object):
    """Set Bugzilla login cookies from auth backend."""

    def process_response(self, request, response):
        print '************************ bugzilla cookie middleware'
        return response
        #if ('reviewboard.accounts.backends.BugzillaBackend'
        #    not in settings.AUTHENTICATION_BACKENDS):
        #    return response

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
