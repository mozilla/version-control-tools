#!/usr/bin/env python
# Unit tests for pushlog / json-pushes

import sys
import unittest
import os.path
from os.path import join, isdir
from mercurial import ui, hg, commands, util
from mercurial.commands import add, clone, commit, init, push
from mercurial.hgweb import server
from subprocess import check_call, Popen, STDOUT, PIPE
import os
import stat
from signal import SIGTERM
from httplib import HTTPConnection
from urllib import urlopen
from time import sleep
from tempfile import mkdtemp
import simplejson
import feedparser
import shutil
import threading
from urlparse import urljoin

mydir = os.path.abspath(os.path.dirname(__file__))
devnull = file("/dev/null", "w")

#==============================
# utility functions and classes
def write_hgrc(repodir):
    with open(join(repodir, ".hg", "hgrc"), "w") as f:
        f.write("""[extensions]
pushlog-feed=%s/pushlog-feed.py
buglink=%s/buglink.py
hgwebjson=%s/hgwebjson.py
[web]
templates=%s
style=gitweb_mozilla
""" % (mydir, mydir, mydir, os.environ['HG_TEMPLATES']))

def pull_templates(path):
    """Clone the hg_templates repo to |path|."""
    # need to grab the moz hg templates
    clone(ui.ui(), "http://hg.mozilla.org/hg_templates/", path);

def loadjsonfile(f):
    """Given a file path relative to the srcdir, load the file as a JSON object."""
    f = file(os.path.join(mydir, f))
    j = simplejson.loads(''.join(f.readlines()))
    f.close()
    return j

class myui(ui.ui):
    """
    Override some config options:
    web.port to get a random port for the server
    web.accesslog to send the access log to /dev/null
    """
    def config(self, section, name, default=None, untrusted=False):
      if section == "web":
          if name == "port":
              return 0
          if name == "accesslog":
              return "/dev/null"
      return ui.ui.config(self, section, name, default, untrusted)

class HGWebTest:
    """A mixin that starts a hgweb server and other niceties."""
    def setUp(self):
        self.ui = myui()
        self.repodir = mkdtemp()
        # subclasses should override this to do real work
        self.setUpRepo()
        write_hgrc(self.repodir)
        self.repo = hg.repository(self.ui, self.repodir)
        self.server = server.create_server(self.ui, self.repo)
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
        j = simplejson.loads(''.join(u.readlines()))
        u.close()
        return j

#==============================
# tests

class TestEmptyRepo(HGWebTest, unittest.TestCase):
    def setUpRepo(self):
        # create an empty repo
        init(self.ui, dest=self.repodir)

    def testemptyrepo(self):
        """Accessing /pushlog on a repo without a pushlog db should succeed"""
        # just GET /pushlog and verify that it's 200 OK
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        self.assertEqual(r.status, 200, "empty pushlog should not error (got HTTP status %d, expected 200)" % r.status)

    def testemptyreporeadonly(self):
        """Accessing /pushlog on a read-only empty repo should succeed."""
        # just GET /pushlog and verify that it's 200 OK
        def rchmod(canWrite = False):
            w = 0
            if canWrite:
                w = stat.S_IWRITE
            for dir, subdirs, files in os.walk(self.repodir):
                os.chmod(dir, stat.S_IREAD + stat.S_IEXEC + w)
                for f in files:
                    os.chmod(os.path.join(dir, f), stat.S_IREAD)
            pass
        rchmod()
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        rchmod(True)
        self.assertEqual(r.status, 200, "empty pushlog should not error (got HTTP status %d, expected 200)" % r.status)

class TestPushlog(HGWebTest, unittest.TestCase):
    def setUp(self):
        HGWebTest.setUp(self)
        os.environ['TZ'] = "America/New_York"

    def setUpRepo(self):
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo.tar.bz2")
        check_call(["tar", "xjf", repoarchive], cwd=self.repodir)

    def testpushloghtml(self):
        """Sanity check the html output."""
        u = self.urlopen("/pushloghtml")
        data = ''.join(u.readlines())
        u.close()
        # ensure we didn't hit a server error in the middle
        self.assertEqual(data.find("Internal Server Error"), -1, "should not get an internal server error in the html output")
        # crap test, but I don't want to parse html
        self.assertNotEqual(data.find("427bfb5defee"), -1, "should have the latest changeset in the html output")
        
    def testalljsonpushes(self):
        """Get all json data from json-pushes."""
        testjson = self.loadjsonurl("/json-pushes?startID=0")
        expectedjson = loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testprintpushlog(self):
        """Get all json data via 'hg printpushlog'."""
        testjson = simplejson.loads(Popen(["hg", "-R", self.repodir, "printpushlog"], stdout=PIPE).communicate()[0])
        expectedjson = loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "printpushlog did not yield expected json data!")

    def testaccesscontrolatom(self):
        """Ensure that /pushlog feed sends Access-Control-Allow-Origin headers."""
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        h = r.getheader("Access-Control-Allow-Origin", None)
        self.assertEqual(h, "*", "/pushlog should send Access-Control-Allow-Origin")

    def testaccesscontroljson(self):
        """Ensure that /json-pushes sends Access-Control-Allow-Origin headers."""
        conn = HTTPConnection("localhost", self.port)
        conn.request("GET", "/json-pushes")
        r = conn.getresponse()
        conn.close()
        h = r.getheader("Access-Control-Allow-Origin", None)
        self.assertEqual(h, "*", "/json-pushes should send Access-Control-Allow-Origin")

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

    def testfromchangetoendidquery(self):
        """Query with fromchange and an endID."""
        testjson = self.loadjsonurl("/json-pushes?fromchange=cc07cc0e87f8&endID=15")
        expectedjson = loadjsonfile("testdata/test-repo-fromchange-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartidtochangequery(self):
        """Query with a startID and tochange."""
        testjson = self.loadjsonurl("/json-pushes?startID=5&tochange=af5fb85d9324")
        expectedjson = loadjsonfile("testdata/test-repo-startid-tochange-query.json")
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

    def testsinglechangesetquery(self):
        """Query for a single changeset."""        
        testjson = self.loadjsonurl("/json-pushes?changeset=91826025c77c")
        expectedjson = loadjsonfile("testdata/test-repo-changeset-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultichangesetquery(self):
        """Query for two changesets at once."""
        testjson = self.loadjsonurl("/json-pushes?changeset=91826025c77c&changeset=a79451771352")
        expectedjson = loadjsonfile("testdata/test-repo-multi-changeset-query.json")
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
    if sys.version[:3] < '2.6':
        # sucks, but it's just a hassle to get BaseServer.shutdown() otherwise
        print >>sys.stderr, "This script requires Python 2.6 or newer"
        sys.exit(1)

    if 'HG_TEMPLATES' not in os.environ or not isdir(os.environ['HG_TEMPLATES']):
        os.environ['HG_TEMPLATES'] = mkdtemp()
        pull_templates(os.environ['HG_TEMPLATES'])
        madeTemplatePath = True
    else:
        madeTemplatePath = False

    unittest.main()
    if madeTemplatePath:
        shutil.rmtree(os.environ['HG_TEMPLATES'])
