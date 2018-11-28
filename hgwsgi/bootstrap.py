# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file contains common code that is executed by every hgweb.wsgi
# WSGI entrypoint.

import os

os.environ['HGENCODING'] = 'UTF-8'


from mercurial.hgweb import hgweb


def make_application(wsgi_dir):
    config = os.path.join(wsgi_dir, 'hgweb.config')

    return hgweb(config)
