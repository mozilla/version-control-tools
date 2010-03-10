#!/usr/bin/env python
# Unit tests for pushlog / json-pushes

import unittest
import os.path
from os.path import join, isdir
from mercurial import ui, hg, commands, util
from mercurial.commands import add, clone, commit, init, push
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

mydir = os.path.abspath(os.path.dirname(__file__))
devnull = file("/dev/null", "w")

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

def loadjsonurl(url):
    """Load JSON from a URL into an object."""
    u = urlopen(url)
    j = simplejson.loads(''.join(u.readlines()))
    u.close()
    return j

def loadjsonfile(f):
    """Given a file path relative to the srcdir, load the file as a JSON object."""
    f = file(os.path.join(mydir, f))
    j = simplejson.loads(''.join(f.readlines()))
    f.close()
    return j

class TestEmptyRepo(unittest.TestCase):
    hgwebprocess = None
    def setUp(self):
        # create an empty repo
        self.repodir = mkdtemp()
        init(ui.ui(), dest=self.repodir)
        write_hgrc(self.repodir)
        # now run hg serve on it
        self.hgwebprocess = Popen(["hg", "-R", self.repodir, "serve"], stdout=devnull, stderr=STDOUT)
        # give it a second to be ready
        sleep(1)

    def tearDown(self):
        # kill hgweb process
        if self.hgwebprocess is not None:
            os.kill(self.hgwebprocess.pid, SIGTERM)
            self.hgwebprocess = None
        shutil.rmtree(self.repodir)

    def testemptyrepo(self):
        """Accessing /pushlog on a repo without a pushlog db should succeed"""
        # just GET /pushlog and verify that it's 200 OK
        conn = HTTPConnection("localhost", 8000)
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
        conn = HTTPConnection("localhost", 8000)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        rchmod(True)
        self.assertEqual(r.status, 200, "empty pushlog should not error (got HTTP status %d, expected 200)" % r.status)

class TestPushlog(unittest.TestCase):
    hgwebprocess = None
    repodir = ''

    def setUp(self):
        "Untar the test repo and add the pushlog extension to it."
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo.tar.bz2")
        self.repodir = mkdtemp()
        check_call(["tar", "xjf", repoarchive], cwd=self.repodir)
        write_hgrc(self.repodir)
        # now run hg serve on it
        self.hgwebprocess = Popen(["hg", "-R", self.repodir, "serve"], stdout=devnull, stderr=STDOUT)
        # give it a second to be ready
        sleep(1)
        os.environ['TZ'] = "America/New_York"

    def tearDown(self):
        # kill hgweb process
        if self.hgwebprocess is not None:
            os.kill(self.hgwebprocess.pid, SIGTERM)
            self.hgwebprocess = None
        shutil.rmtree(self.repodir)

    def testpushloghtml(self):
        """Sanity check the html output."""
        u = urlopen("http://localhost:8000/pushloghtml")
        data = ''.join(u.readlines())
        u.close()
        # ensure we didn't hit a server error in the middle
        self.assertEqual(data.find("Internal Server Error"), -1, "should not get an internal server error in the html output")
        # crap test, but I don't want to parse html
        self.assertNotEqual(data.find("427bfb5defee"), -1, "should have the latest changeset in the html output")
        
    def testalljsonpushes(self):
        """Get all json data from json-pushes."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startID=0")
        expectedjson = loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testprintpushlog(self):
        """Get all json data via 'hg printpushlog'."""
        testjson = simplejson.loads(Popen(["hg", "-R", self.repodir, "printpushlog"], stdout=PIPE).communicate()[0])
        expectedjson = loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "printpushlog did not yield expected json data!")

    def testaccesscontrolatom(self):
        """Ensure that /pushlog feed sends Access-Control-Allow-Origin headers."""
        conn = HTTPConnection("localhost", 8000)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        h = r.getheader("Access-Control-Allow-Origin", None)
        self.assertEqual(h, "*", "/pushlog should send Access-Control-Allow-Origin")

    def testaccesscontroljson(self):
        """Ensure that /json-pushes sends Access-Control-Allow-Origin headers."""
        conn = HTTPConnection("localhost", 8000)
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
        testfeed = feedparser.parse("http://localhost:8000/pushlog")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-latest-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpage2pushlogatom(self):
        """Get the second page of 10 pushes via pushlog/2."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog/2")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-page-2-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpushlogatom(self):
        """Get all ATOM data via pushlog."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?startdate=2008-11-20%2010:50:00&enddate=2008-11-20%2010:54:00")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpartialdatequeryatom(self):
        """Get some ATOM data via pushlog date query."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:25")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testchangesetqueryatom(self):
        """Get some ATOM data via pushlog changeset query."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?fromchange=4ccee53e18ac&tochange=a79451771352")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-changeset-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testtipsonlyatom(self):
        """Get only the tips as ATOM data from pushlog?tipsonly=1."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?tipsonly=1")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testpartialdatequerytipsonlyatom(self):
        """Get some tipsonly ATOM data via pushlog date query."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:25&tipsonly=1")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testchangesetquerytipsonlyatom(self):
        """Get some tipsonly ATOM data via pushlog changeset query."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?fromchange=4ccee53e18ac&tochange=a79451771352&tipsonly=1")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-changeset-query-tipsonly-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def testdatequerytrailingspaceatom(self):
        """Dates with leading/trailing spaces should work properly."""
        testfeed = feedparser.parse("http://localhost:8000/pushlog?startdate=%202008-11-20%2010:52:25%20&enddate=%202008-11-20%2010:53:25%20&foo=bar")
        expectedfeed = feedparser.parse(os.path.join(mydir, "testdata/test-repo-date-query-data.xml"))
        self.assertEqualFeeds(testfeed, expectedfeed)

    def teststartidtoenddatequery(self):
        """Query with a startID and an enddate."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startID=5&enddate=2008-11-20%2010:53:25")
        expectedjson = loadjsonfile("testdata/test-repo-startid-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetoendidquery(self):
        """Query with a startdate and an endID."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&endID=15")
        expectedjson = loadjsonfile("testdata/test-repo-startdate-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testfromchangetoendidquery(self):
        """Query with fromchange and an endID."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?fromchange=cc07cc0e87f8&endID=15")
        expectedjson = loadjsonfile("testdata/test-repo-fromchange-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartidtochangequery(self):
        """Query with a startID and tochange."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startID=5&tochange=af5fb85d9324")
        expectedjson = loadjsonfile("testdata/test-repo-startid-tochange-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testfromchangetoenddatequery(self):
        """Query with fromchange and an enddate."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?fromchange=cc07cc0e87f8&enddate=2008-11-20%2010:52:56")
        expectedjson = loadjsonfile("testdata/test-repo-fromchange-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetochangequery(self):
        """Query with a startdate and tochange."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&tochange=af5fb85d9324")
        expectedjson = loadjsonfile("testdata/test-repo-startdate-tochange-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testsinglechangesetquery(self):
        """Query for a single changeset."""        
        testjson = loadjsonurl("http://localhost:8000/json-pushes?changeset=91826025c77c")
        expectedjson = loadjsonfile("testdata/test-repo-changeset-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultichangesetquery(self):
        """Query for two changesets at once."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?changeset=91826025c77c&changeset=a79451771352")
        expectedjson = loadjsonfile("testdata/test-repo-multi-changeset-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testdateparsing(self):
        """Test that we can parse partial dates, missing seconds, minutes, hours."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53:00")
        expectedjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2010:53")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds")
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2011:00:00")
        expectedjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-20%2011")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds and minutes")
        testjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-21%2000:00:00")
        expectedjson = loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&enddate=2008-11-21")
        self.assertEqual(testjson, expectedjson, "Failed to parse date with missing seconds, minutes, hours")

class TestPushlogUserQueries(unittest.TestCase):
    hgwebprocess = None
    repodir = ''

    def setUp(self):
        "Untar the test repo and add the pushlog extension to it."
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo-users.tar.bz2")
        self.repodir = mkdtemp()
        check_call(["tar", "xjf", repoarchive], cwd=self.repodir)
        write_hgrc(self.repodir)
        # now run hg serve on it
        self.hgwebprocess = Popen(["hg", "-R", self.repodir, "serve"], stdout=devnull, stderr=STDOUT)
        # give it a second to be ready
        sleep(1)
        os.environ['TZ'] = "America/New_York"

    def tearDown(self):
        # kill hgweb process
        if self.hgwebprocess is not None:
            os.kill(self.hgwebprocess.pid, SIGTERM)
            self.hgwebprocess = None

    def testuserquery(self):
        """Query for an individual user's pushes."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=luser")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=someone")
        expectedjson = loadjsonfile("testdata/test-repo-user-someone.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultiuserquery(self):
        """Query for two users' pushes."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=luser&user=someone")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-someone.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testmultiuserstartidquery(self):
        """Querying for all users' pushes + a startID should be equivalent to just querying for that startID."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=luser&user=someone&user=johndoe&startID=20")
        expectedjson = loadjsonurl("http://localhost:8000/json-pushes?startID=20")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testuserstartdatequery(self):
        """Query for a user and a startdate."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=luser&startdate=2008-11-21%2011:36:40")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-startdate.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testuserstartdateenddatequery(self):
        """Query for a user with a startdate and an enddate."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?user=luser&startdate=2008-11-21%2011:36:40&enddate=2008-11-21%2011:37:10")
        expectedjson = loadjsonfile("testdata/test-repo-user-luser-startdate-enddate.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testchangesetsanduserquery(self):
        """Query for multiple changesets and a user, should be the same as just querying for the one changeset, as only one changeset was pushed by this user."""
        testjson = loadjsonurl("http://localhost:8000/json-pushes?changeset=edd2698e8172&changeset=4eb202ea0252&user=luser")
        expectedjson = loadjsonurl("http://localhost:8000/json-pushes?changeset=edd2698e8172")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

if __name__ == '__main__':
    if 'HG_TEMPLATES' not in os.environ or not isdir(os.environ['HG_TEMPLATES']):
        os.environ['HG_TEMPLATES'] = mkdtemp()
        pull_templates(os.environ['HG_TEMPLATES'])
        madeTemplatePath = True
    else:
        madeTemplatePath = False

    unittest.main()
    if madeTemplatePath:
        shutil.rmtree(os.environ['HG_TEMPLATES'])
