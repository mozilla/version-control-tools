#!/usr/bin/env python

config = "/repo/hg/webroot_wsgi/releases/l10n/mozilla-release/hgweb.config"

from mercurial.hgweb import hgweb

import os
os.environ["HGENCODING"] = "UTF-8"

application = hgweb(config)

