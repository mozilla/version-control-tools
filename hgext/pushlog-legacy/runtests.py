#!/usr/bin/python
# I'm sure this all only works on my mac, but that's ok for now.

import unittest
import os.path
from subprocess import check_call, Popen, STDOUT, PIPE
import os
from signal import SIGTERM
from httplib import HTTPConnection
from urllib import urlopen
from time import sleep
import simplejson
import feedparser

mydir = os.path.abspath(os.path.dirname(__file__))
# where to store needed hg templates repo
templatepath = "/tmp/hg_templates"
devnull = file("/dev/null", "w")

def write_hgrc(repodir):
    f = open(repodir + ".hg/hgrc", "w")
    f.write("""[extensions]
pushlog-feed=%s/pushlog-feed.py
buglink=%s/buglink.py
hgwebjson=%s/hgwebjson.py
[web]
templates=%s
style=gitweb_mozilla
""" % (mydir, mydir, mydir, templatepath))
    f.close()

def ensure_templates():
    # need to grab the moz hg templates
    if not os.path.isdir(templatepath):
        check_call(["hg", "clone", "http://hg.mozilla.org/hg_templates/",
                    templatepath], stdout=devnull, stderr=STDOUT)
    # make sure it's updated
    check_call(["hg","-R",templatepath,"pull","-u"], stdout=devnull, stderr=STDOUT)

class TestEmptyRepo(unittest.TestCase):
    hgwebprocess = None
    def setUp(self):
        # create an empty repo
        repodir = "/tmp/hg-empty-repo/"
        check_call(["rm", "-rf", repodir])
        os.mkdir(repodir)
        check_call(["hg","init",repodir])
        write_hgrc(repodir)
        ensure_templates()
        # now run hg serve on it
        self.hgwebprocess = Popen(["hg", "-R", repodir, "serve"], stdout=devnull, stderr=STDOUT)
        # give it a second to be ready
        sleep(1)

    def tearDown(self):
        # kill hgweb process
        if self.hgwebprocess is not None:
            os.kill(self.hgwebprocess.pid, SIGTERM)
            self.hgwebprocess = None

    def testemptyrepo(self):
        # just GET /pushlog and verify that it's 200 OK
        conn = HTTPConnection("localhost", 8000)
        conn.request("GET", "/pushlog")
        r = conn.getresponse()
        conn.close()
        self.assertEqual(r.status, 200, "empty pushlog should not error (got HTTP status %d, expected 200)" % r.status)

class TestPushlog(unittest.TestCase):
    hgwebprocess = None
    repodir = ''

    def setUp(self):
        "Untar the test repo and add the pushlog extension to it."
        # unpack the test repo
        repoarchive = os.path.join(mydir, "testdata/test-repo.tar.bz2")
        repodir = "/tmp/hg-test/"
        self.repodir = repodir
        check_call(["rm", "-rf", repodir])
        check_call(["tar", "xjf", repoarchive], cwd="/tmp")
        write_hgrc(repodir)
        ensure_templates()
        # now run hg serve on it
        self.hgwebprocess = Popen(["hg", "-R", repodir, "serve"], stdout=devnull, stderr=STDOUT)
        # give it a second to be ready
        sleep(1)
        os.environ['TZ'] = "America/New_York"

    def tearDown(self):
        # kill hgweb process
        if self.hgwebprocess is not None:
            os.kill(self.hgwebprocess.pid, SIGTERM)
            self.hgwebprocess = None

    def loadjsonurl(self, url):
        """Load JSON from a URL into an object."""
        u = urlopen(url)
        j = simplejson.loads(''.join(u.readlines()))
        u.close()
        return j

    def loadjsonfile(self, f):
        """Given a file path relative to the srcdir, load the file as a JSON object."""
        f = file(os.path.join(mydir, f))
        j = simplejson.loads(''.join(f.readlines()))
        f.close()
        return j
        
    def testalljsonpushes(self):
        """Get all json data from json-pushes."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?startID=0")
        expectedjson = self.loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testprintpushlog(self):
        """Get all json data via 'hg printpushlog'."""
        testjson = simplejson.loads(Popen(["hg", "-R", self.repodir, "printpushlog"], stdout=PIPE).communicate()[0])
        expectedjson = self.loadjsonfile("testdata/test-repo-data.json")
        self.assertEqual(testjson, expectedjson, "printpushlog did not yield expected json data!")

    def assertEqualFeeds(self, a, b):
        self.assertEqual(a.feed.title, b.feed.title, "not the same title, %s != %s" % (a.feed.title, b.feed.title))
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
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?startID=5&enddate=2008-11-20%2010:53:25")
        expectedjson = self.loadjsonfile("testdata/test-repo-startid-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetoendidquery(self):
        """Query with a startdate and an endID."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&endID=15")
        expectedjson = self.loadjsonfile("testdata/test-repo-startdate-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testfromchangetoendidquery(self):
        """Query with fromchange and an endID."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?fromchange=cc07cc0e87f8&endID=15")
        expectedjson = self.loadjsonfile("testdata/test-repo-fromchange-endid-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartidtochangequery(self):
        """Query with a startID and tochange."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?startID=5&tochange=af5fb85d9324")
        expectedjson = self.loadjsonfile("testdata/test-repo-startid-tochange-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def testfromchangetoenddatequery(self):
        """Query with fromchange and an enddate."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?fromchange=cc07cc0e87f8&enddate=2008-11-20%2010:52:56")
        expectedjson = self.loadjsonfile("testdata/test-repo-fromchange-enddate-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

    def teststartdatetochangequery(self):
        """Query with a startdate and tochange."""
        testjson = self.loadjsonurl("http://localhost:8000/json-pushes?startdate=2008-11-20%2010:52:25&tochange=af5fb85d9324")
        expectedjson = self.loadjsonfile("testdata/test-repo-startdate-tochange-query.json")
        self.assertEqual(testjson, expectedjson, "json-pushes did not yield expected json data!")

if __name__ == '__main__':
    unittest.main()
