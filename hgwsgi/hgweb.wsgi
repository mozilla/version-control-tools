# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# Path to repo or hgweb config to serve (see 'hg help hgweb')
config = "/repo/hg/webroot_wsgi/hgweb.config"

from mercurial.hgweb import hgweb

import os
os.environ["HGENCODING"] = "UTF-8"

application = hgweb(config)
