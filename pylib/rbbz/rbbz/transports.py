# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import urlparse
import xmlrpclib


class CookieTransportMixin:
    """A Transport request method that retains cookies over its lifetime.

    Adapted directly from http://www.lunch.org.uk/wiki/xmlrpccookies with
    permission from the author.

    The regular xmlrpclib transports ignore cookies, which causes
    a bit of a problem when you need a cookie-based login, as with
    the Bugzilla XMLRPC interface.

    So this is a helper for defining a Transport which looks for
    cookies being set in responses and saves them to add to all future
    requests.
    """

    # Inspiration drawn from
    # http://blog.godson.in/2010/09/how-to-make-python-xmlrpclib-client.html
    # http://www.itkovian.net/base/transport-class-for-pythons-xml-rpc-lib/
    #
    # Note this must be an old-style class so that __init__ handling works
    # correctly with the old-style Transport class. If you make this class
    # a new-style class, Transport.__init__() won't be called.

    cookies = []

    def send_cookies(self, connection):
        if self.cookies:
            for cookie in self.cookies:
                connection.putheader("Cookie", cookie)

    def request(self, host, handler, request_body, verbose=0):
        self.verbose = verbose

        # issue XML-RPC request
        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_cookies(h)
        self.send_user_agent(h)
        self.send_content(h, request_body)

        # Deal with differences between Python 2.4-2.6 and 2.7.
        # In the former h is a HTTP(S). In the latter it's a
        # HTTP(S)Connection. Luckily, the 2.4-2.6 implementation of
        # HTTP(S) has an underlying HTTP(S)Connection, so extract
        # that and use it.
        try:
            response = h.getresponse()
        except AttributeError:
            response = h._conn.getresponse()

        # Add any cookie definitions to our list.
        for header in response.msg.getallmatchingheaders("Set-Cookie"):
            val = header.split(": ", 1)[1]
            cookie = val.split(";", 1)[0]
            self.cookies.append(cookie)

        if response.status != 200:
            raise xmlrpclib.ProtocolError(host + handler, response.status,
                                          response.reason,
                                          response.msg.headers)

        payload = response.read()
        parser, unmarshaller = self.getparser()
        parser.feed(payload)
        parser.close()

        return unmarshaller.close()


class BugzillaTransportMixin(CookieTransportMixin):

    LOGIN = 'Bugzilla_login'
    LOGIN_COOKIE = 'Bugzilla_logincookie'

    def remove_bugzilla_cookies(self):
        self.cookies = [x for x in self.cookies
                        if not x.startswith('%s=' % self.LOGIN) and
                        not x.startswith('%s=' % self.LOGIN_COOKIE)]

    def set_bugzilla_cookies(self, login, login_cookie):
        self.remove_bugzilla_cookies()
        self.cookies.append('%s=%s' % (self.LOGIN, login))
        self.cookies.append('%s=%s' % (self.LOGIN_COOKIE, login_cookie))

    def set_bugzilla_cookies_from_request(self, request):
        try:
            bzlogin = request.session['Bugzilla_login']
            bzcookie = request.session['Bugzilla_logincookie']
        except KeyError:
            return False

        self.set_bugzilla_cookies(bzlogin, bzcookie)
        return True

    def bugzilla_cookies(self):
        login = ''
        login_cookie = ''

        for c in self.cookies:
            name, _, val = c.partition('=')

            if name == self.LOGIN:
                login = val
            elif name == self.LOGIN_COOKIE:
                login_cookie = val

        return (login, login_cookie)


class BugzillaTransport(BugzillaTransportMixin, xmlrpclib.Transport):
    pass


class BugzillaSafeTransport(BugzillaTransportMixin, xmlrpclib.SafeTransport):
    pass


def bugzilla_transport(uri):
    """Return an appropriate Transport for the URI.

    If the URI type is https, return a CookieSafeTransport.
    If the type is http, return a CookieTransport.
    """
    if urlparse.urlparse(uri, "http")[0] == "https":
        return BugzillaSafeTransport()

    return BugzillaTransport()
