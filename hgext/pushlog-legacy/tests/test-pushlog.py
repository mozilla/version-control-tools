#!/usr/bin/env python
# Unit tests for pushlog / json-pushes

import unittest
import silenttestrunner
import os.path
import inspect
from os.path import join
from mercurial import ui, hg
from mercurial.hgweb import server
import mercurial.hgweb as hgweb
from subprocess import check_call
import os
from urllib import urlopen
from tempfile import mkdtemp
import json
import feedparser
import shutil
import threading
from urlparse import urljoin

here = os.path.abspath(os.path.dirname(__file__))
mydir = os.path.normpath(os.path.join(here, '..'))
root = os.path.normpath(os.path.join(here, '..', '..', '..'))
devnull = file("/dev/null", "w")

HGRC_TEMPLATE = '''
[extensions]
pushlog={root}/hgext/pushlog
pushlog-feed={root}/hgext/pushlog-legacy/pushlog-feed.py
hgmo={root}/hgext/hgmo
[web]
templates={templates}
style=gitweb_mozilla
'''

#==============================
# utility functions and classes
def write_hgrc(repodir):
    with open(join(repodir, ".hg", "hgrc"), "w") as f:
        f.write(HGRC_TEMPLATE.format(
            root=root,
            templates=os.environ['HG_TEMPLATES'],
        ))

def loadjsonfile(f):
    """Given a file path relative to the srcdir, load the file as a JSON object."""
    f = file(os.path.join(mydir, f))
    j = json.loads(''.join(f.readlines()))
    f.close()
    return j

class myui(ui.ui):
    """
    Override some config options:
    web.port to get a random port for the server
    web.accesslog to send the access log to /dev/null
    """
    def config(self, section, name, *args, **kwargs):
      if section == "web":
          if name == "port":
              return 0
          if name == "accesslog":
              return "/dev/null"
      return ui.ui.config(self, section, name, *args, **kwargs)

# We seem to trigger "connection reset by peer" in a lot of our tests,
# which doesn't seem harmful but does litter the test output with
# tracebacks.
def handle_error(request, client_address):
    pass

class HGWebTest:
    """A mixin that starts a hgweb server and other niceties."""
    def setUp(self):
        self.ui = myui()
        self.repodir = mkdtemp()
        # subclasses should override this to do real work
        self.setUpRepo()
        write_hgrc(self.repodir)
        self.repo = hg.repository(self.ui, self.repodir)
        # At some point create_server changed to take a hgweb.hgweb
        # as the second param instead of a repo. I don't know of a clean
        # way to feature test this, and this is just a unit test, so
        # the hacky way seems okay.
        argname = inspect.getargspec(server.create_server).args[1]
        arg = None
        if argname == "app":
            arg = hgweb.hgweb(self.repo.root, baseui=self.ui)
        elif argname == "repo":
            arg = self.repo
        if arg is None:
            # error, something unknown
            raise SystemExit("Don't know how to run hgweb in this Mercurial version!")
        self.server = server.create_server(self.ui, arg)
        self.server.handle_error = handle_error
        _, self.port = self.server.socket.getsockname()
        # run the server on a background thread so we can interrupt it
        threading.Thread(target=self.server.serve_forever).start()

    def setUpRepo(self):
        """Initialize the repository in self.repodir for testing"""
        pass

    def tearDown(self):
        if self.server:
            self.server.shutdown()
        shutil.rmtree(self.repodir)

    def urlopen(self, url):
        """Convenience function to open URLs on the local server."""
        return urlopen(urljoin("http://localhost:%d" % self.port, url))

    def loadjsonurl(self, url):
        """Convenience function to load JSON from a URL into an object."""
        u = self.urlopen(url)
        j = json.loads(''.join(u.readlines()))
        u.close()
        return j

#==============================
# tests
class TestPushlogUserQueries(HGWebTest, unittest.TestCase):
    def setUp(self):
        HGWebTest.setUp(self)
        os.environ['TZ'] = "America/New_York"

    def setUpRepo(self):
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo-users.tar.bz2")
        check_call(["tar", "xjf", repoarchive], cwd=self.repodir)

    def testuserquery(self):
        """Query for an individual user's pushes."""
        testjson = self.loadjsonurl("/json-pushes?user=luser")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")
        testjson = self.loadjsonurl("/json-pushes?user=someone")
        expectedjson = loadjsonfile("testdata/test-repo-user-someone.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultiuserquery(self):
        """Query for two users' pushes."""
        testjson = self.loadjsonurl("/json-pushes?user=luser&user=someone")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-someone.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultiuserstartidquery(self):
        """Querying for all users' pushes + a startID should be equivalent to just querying for that startID."""
        testjson = self.loadjsonurl("/json-pushes?user=luser&user=someone&user=johndoe&startID=20")
        expectedjson = self.loadjsonurl("/json-pushes?startID=20")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testuserstartdatequery(self):
        """Query for a user and a startdate."""
        testjson = self.loadjsonurl("/json-pushes?user=luser&startdate=2008-11-21%2011:36:40")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-startdate.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testuserstartdateenddatequery(self):
        """Query for a user with a startdate and an enddate."""
        testjson = self.loadjsonurl("/json-pushes?user=luser&startdate=2008-11-21%2011:36:40&enddate=2008-11-21%2011:37:10")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-startdate-enddate.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testchangesetsanduserquery(self):
        """Query for multiple changesets and a user, should be the same as just querying for the one changeset, as only one changeset was pushed by this user."""
        testjson = self.loadjsonurl("/json-pushes?changeset=edd2698e8172&changeset=4eb202ea0252&user=luser")
        expectedjson = self.loadjsonurl("/json-pushes?changeset=edd2698e8172")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

if __name__ == '__main__':
    template_dir = os.path.normpath(os.path.abspath(
        os.path.join(here, '..', '..', '..', 'hgtemplates')))
    os.environ['HG_TEMPLATES'] = template_dir

    silenttestrunner.main(__name__)
