#!/usr/bin/env python

config = "/repo/hg/webroot_wsgi/aurora-l10n/hgweb.config"

from mercurial import demandimport; demandimport.enable()
from mercurial.hgweb import hgweb

import os
os.environ["HGENCODING"] = "UTF-8"

application = hgweb(config)

