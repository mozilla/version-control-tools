# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""
Advanced URL Interceptor extension to intercept URL requests originating from
mercurial.urllibcompat and mock the response instead of sending any real
requests.

The interceptor can be configured using a JSON file consisting of URLs as keys,
and data and/or status code as values.

Here is an example configuration:

    {
        "https://example.org/": {"code": 200, "data": "Hello, world!"},
        "https://example.com/": {"code": 404},
        "https://example.ca/": {"code": null},
    }

In the above configuration, the interceptor will return a 200 status code and
"Hello, world!" as the body if a request is made to https://example.org/. It
will raise an HTTPError with a status code of 404 if a request is made to
https://example.com/, and it will raise a URLError if a request is made to
https://example.ca/.

Possible values for "code" include an integer (this will be used directly when
creating the HTTPError exception), or None (null in JSON) which will cause a
URLError to be raised.
"""
import io
import json

from mercurial import (
    error,
    pycompat,
    registrar,
    url,
    urllibcompat,
)

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b"advancedurlintercept", b"path", default=None)


class AdvancedURLInterceptor(object):
    def __init__(self, ui):
        self.ui = ui

    def open(self, req, data=None):
        """
        Args:
            req (Request)

        Returns:
            io.BytesIO object with extra `getcode` attribute.

        Raises:
            HTTPError, URLError
        """
        path = self.ui.config(b"advancedurlintercept", b"path")
        if not path:
            raise error.Abort(b"no urlintercept path defined!")

        with open(path, "rb") as fh:
            data = json.load(fh)

        response = data[req.get_full_url()]

        if response["code"] is None:
            # No response, i.e. raise URLError
            raise urllibcompat.urlerr.urlerror(b"fake error")

        if response["code"] != 200:
            raise urllibcompat.urlerr.httperror(url, response["code"], b"", None, None)

        return_obj = io.BytesIO(pycompat.bytestr(json.dumps(response["data"])))

        # Urllib "openers" expect a file-like object with some
        # extra helper parameters. Add them here.
        return_obj.getcode = lambda: 200

        return return_obj


def extsetup(ui):
    interceptor = AdvancedURLInterceptor(ui)
    url.urlreq.installopener(interceptor)
