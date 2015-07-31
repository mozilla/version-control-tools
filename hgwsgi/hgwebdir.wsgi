#!/usr/bin/env python

from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial.hgweb.request import wsgiapplication

import os
os.environ["HGENCODING"] = "UTF-8"

def make_web_app():
    return hgwebdir("/repo/hg/webroot_wsgi/hgweb.config")

application = wsgiapplication(make_web_app)

