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

import urllib2
from StringIO import StringIO

from mercurial import (
    registrar,
    util,
)


# TRACKING hg43 Mercurial 4.3 introduced the config registrar. 4.4
# requires config items to be registered to avoid a devel warning.
if util.safehasattr(registrar, 'configitem'):
    configtable = {}
    configitem = registrar.configitem(configtable)

    configitem('urlintercept', 'path',
               default=None)


class URLInterceptor(object):
    def __init__(self, ui):
        self.ui = ui

    def open(self, url, data=None, timeout=None):
        path = self.ui.config('urlintercept', 'path')
        if not path:
            raise util.Abort('no urlintercept path defined!')

        with open(path, 'rb') as fh:
            expected = fh.readline().rstrip()
            response = fh.read()

        if url != expected:
            raise util.Abort('Incorrect URL. Got %s; expected %s' % (
                url, expected))

        self.ui.write('intercepting url\n')
        return StringIO(response)

def extsetup(ui):
    interceptor = URLInterceptor(ui)
    urllib2.install_opener(interceptor)
