# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file contains common code that is executed by every hgweb.wsgi
# WSGI entrypoint.

import errno
import os

# Set this before importing mercurial.* modules.
os.environ['HGENCODING'] = 'UTF-8'


from mercurial.hgweb import hgwebdir
from mercurial import pycompat


# Set HTTPS_PROXY from /etc/environment value, if present. We don't
# source /etc/environment completely because we have no need for
# some of its variables. And HTTP_PROXY could confuse WSGI into
# thinking the client sent a "Proxy: " request header.
def set_env():
    try:
        with open('/etc/environment', 'rb') as fh:
            for line in fh:
                if not line.startswith(b'HTTPS_PROXY='):
                    continue

                value = line.strip().split(b'=', 1)[1]
                value = value.strip(b'"')

                os.environ['HTTPS_PROXY'] = pycompat.strurl(value)
                break

    except IOError as e:
        if e.errno != errno.ENOENT:
            raise


def make_application(wsgi_dir):
    set_env()

    config = os.path.join(wsgi_dir, 'hgweb.config')

    return hgwebdir(pycompat.bytestr(config))
