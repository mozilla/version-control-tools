# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy extension to intercept URL requests and respond with mocked
response.

This extension works by reading state from a well-defined file. That
file contains the URL being fetched and the content that should be
returned by that URL.

Currently, some defaults are assumed. Functionality can be expanded as
needed.
"""

from mercurial import (
    error,
    pycompat,
    registrar,
    url,
)

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'urlintercept', b'path',
           default=None)

class URLInterceptor(object):
    def __init__(self, ui):
        self.ui = ui

    def open(self, url, data=None, timeout=None):
        path = self.ui.config(b'urlintercept', b'path')
        if not path:
            raise error.Abort(b'no urlintercept path defined!')

        with open(path, 'rb') as fh:
            expected = fh.readline().rstrip()
            response = fh.read()

        if url != expected:
            raise error.Abort(b'Incorrect URL. Got %s; expected %s' % (
                url, expected))

        self.ui.write(b'intercepting url\n')
        return pycompat.bytesio(response)

def extsetup(ui):
    interceptor = URLInterceptor(ui)
    url.urlreq.installopener(interceptor)
