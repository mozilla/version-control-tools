config = "/repo_local/mozilla/webroot_wsgi/hgweb.config"
from mercurial import demandimport; demandimport.enable()
from mercurial.hgweb import hgweb
import os
os.environ["HGENCODING"] = "UTF-8"
application = hgweb(config)
