# Path to repo or hgweb config to serve (see 'hg help hgweb')
config = "/repo/hg/webroot_wsgi/hgweb.config"

from mercurial.hgweb import hgweb

import os
os.environ["HGENCODING"] = "UTF-8"

application = hgweb(config)
