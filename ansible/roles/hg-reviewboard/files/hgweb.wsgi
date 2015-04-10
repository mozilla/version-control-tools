import os
os.environ["HGENCODING"] = "UTF-8"

config = "/repo/hg/webroot_wsgi/hgweb.config"

from mercurial import demandimport; demandimport.enable()
from mercurial.hgweb import hgweb

application = hgweb(config)
