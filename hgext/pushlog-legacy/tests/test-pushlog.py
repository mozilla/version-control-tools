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

class TestPushlog(HGWebTest, unittest.TestCase):
    def setUp(self):
        HGWebTest.setUp(self)
        os.environ['TZ'] = "America/New_York"

    def setUpRepo(self):
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo.tar.bz2")
        check_call(["tar", "xjf", repoarchive], cwd=self.repodir)

    def assertEqualFeeds(self, a, b):
        self.assertEqual(a.feed.updated, b.feed.updated, "not the same updated time, %s != %s" % (a.feed.updated, b.feed.updated))
        self.assertEqual(len(a.entries), len(b.entries), "not the same number of entries, %d != %d" % (len(a.entries), len(b.entries)))
        for ae, be in zip(a.entries, b.entries):
            self.assertEqual(ae.updated, be.updated, "not the same updated time, %s != %s" % (ae.updated, be.updated))
            self.assertEqual(ae.title, be.title, "not the same title, %s != %s" % (ae.title, be.title))
            self.assertEqual(ae.id, be.id, "not the same id, %s != %s" % (ae.id, be.id))
            self.assertEqual(ae.author_detail.name, be.author_detail.name, "not the same author, %s != %s" % (ae.author_detail.name, be.author_detail.name))

    def testlatestpushlogatom(self):
        """Get only the latest 10 pushes via pushlog."""
        testfeed = feedparser.parse(self.urlopen("/pushlog"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-latest-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpage2pushlogatom(self):
        """Get the second page of 10 pushes via pushlog/2."""
        testfeed = feedparser.parse(self.urlopen("/pushlog/2"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-page-2-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpushlogatom(self):
        """Get all ATOM data via pushlog."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?startdate=2008-11-20%2010:50:00&enddate=2008-11-20%2010:54:00"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpartialdatequeryatom(self):
        """Get some ATOM data via pushlog date query."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:25"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testchangesetqueryatom(self):
        """Get some ATOM data via pushlog changeset query."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?fromchange=4ccee53e18ac&tochange=a79451771352"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-changeset-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testtipsonlyatom(self):
        """Get only the tips as ATOM data from pushlog?tipsonly=1."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?tipsonly=1"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpartialdatequerytipsonlyatom(self):
        """Get some tipsonly ATOM data via pushlog date query."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:25&tipsonly=1"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testchangesetquerytipsonlyatom(self):
        """Get some tipsonly ATOM data via pushlog changeset query."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?fromchange=4ccee53e18ac&tochange=a79451771352&tipsonly=1"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-changeset-query-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testdatequerytrailingspaceatom(self):
        """Dates with leading/trailing spaces should work properly."""
        testfeed = feedparser.parse(self.urlopen("/pushlog?startdate=%202008-11-20%2010:52:25%20&enddate=%202008-11-20%2010:53:25%20&foo=bar"))
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def teststartidtoenddatequery(self):
        """Query with a startID and an enddate."""
        testjson = self.loadjsonurl("/json-pushes?startID=5&enddate=2008-11-20%2010:53:25")
        expectedjson = loadjsonfile("testdata/test-repo-startid-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetoendidquery(self):
        """Query with a startdate and an endID."""
        testjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&endID=15")
        expectedjson = loadjsonfile("testdata/test-repo-startdate-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testfromchangetoenddatequery(self):
        """Query with fromchange and an enddate."""
        testjson = self.loadjsonurl("/json-pushes?fromchange=cc07cc0e87f8&enddate=2008-11-20%2010:52:56")
        expectedjson = loadjsonfile("testdata/test-repo-fromchange-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetochangequery(self):
        """Query with a startdate and tochange."""
        testjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&tochange=af5fb85d9324")
        expectedjson = loadjsonfile("testdata/test-repo-startdate-tochange-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testdateparsing(self):
        """Test that we can parse partial dates, missing seconds, minutes, hours."""
        testjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:00")
        expectedjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds")
        testjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2011:00:00")
        expectedjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2011")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds and minutes")
        testjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-21%2000:00:00")
        expectedjson = self.loadjsonurl("/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-21")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds, minutes, hours")

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
