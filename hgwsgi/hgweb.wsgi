# Path to repo or hgweb config to serve (see 'hg help hgweb')
config = "/repo/hg/webroot_wsgi/hgweb.config"

# Uncomment and adjust if Mercurial is not installed system-wide
# (consult "installed modules" path from 'hg debuginstall'):
#import sys; sys.path.insert(0, "/usr/lib64/python2.4/site-packages/mercurial")

# Uncomment to send python tracebacks to the browser if an error occurs:
#import cgitb; cgitb.enable()

# enable demandloading to reduce startup time
from mercurial import demandimport; demandimport.enable()

from mercurial.hgweb import hgweb

import os
os.environ["HGENCODING"] = "UTF-8"

application = hgweb(config)
