#!/usr/bin/env python
""" TODO: Rewrite this as a WSGI app"""

from mercurial import demandimport
demandimport.enable()
from mercurial.hgweb import hgweb, wsgicgi
from mercurial import ui, hg
import os

prefix = os.environ["CONTEXT_PREFIX"].split("/", 4)[0:4]

repo = os.environ["CONTEXT_PREFIX"].split("/")[2]
bundle = os.environ["CONTEXT_PREFIX"].split("/")[3]
path = "/".join(os.environ["CONTEXT_PREFIX"].split("/")[4:])

prefix = "/".join(prefix)

os.environ["SCRIPT_NAME"] = prefix
os.environ["PATH_INFO"] = path

fh = open("/tmp/env", "w+")
fh.write(str(os.environ))
fh.close()

if repo is "" or bundle is "":
    print "Content-type: text/html\n\n"
    print "Missing repo or bundle name!"
    exit(1)

if not os.path.isfile('/var/hg/bundles/%s.bundle' % bundle):
    print "Content-type: text/html\n\n"
    print "Error: Bundle '%s' doesn't exist!" % bundle
    exit(1)

if not os.path.isdir('/var/hg/repos/%s' % repo):
    print "Content-type: text/html\n\n"
    print "Error: Repository '%s' doesn't exist!" % repo

u = ui.ui()

u.setconfig('bundle', 'mainreporoot', '/var/hg/repos/%s' % repo)
repo = hg.repository(u, '/var/hg/bundles/%s.bundle' % bundle)

application = hgweb(repo)
wsgicgi.launch(application)
