#!/usr/bin/env python

from __future__ import with_statement
import unittest
from mercurial import ui, hg, commands, util
from mercurial.commands import add, clone, commit, init, push
from mercurial.node import hex
from tempfile import mkdtemp
import shutil
import os, stat
from os.path import join
import sqlite3 as sqlite
from getpass import getuser
from time import time
import urllib2
from StringIO import StringIO

def addHook(repodir, hook):
  with open(join(repodir, '.hg', 'hgrc'), 'w') as f:
    f.write("""[hooks]
pretxnchangegroup.z_linearhistory = python:mozhghooks.%s
""" % hook)

def appendFile(filename, content):
  with open(filename, 'a') as f:
    f.write(content)

def getPushesFromDB(repo):
  conn = sqlite.connect(join(repo.root, '.hg', 'pushlog2.db'))
  res = conn.execute("SELECT id, user, date, rev, node from pushlog INNER JOIN changesets on pushlog.id = changesets.pushid ORDER BY id")
  s = set()
  pushes = []
  for row in res.fetchall():
    if row[0] not in s:
      pushes.append({'id':row[0],
                     'user':row[1],
                     'date':row[2],
                     'changes':[]})
      s.add(row[0])
    pushes[-1]['changes'].append({'rev':row[3], 'node':row[4]})
  return pushes

class TestPushlogHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-test")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "pushlog.log")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)

  def testBasic(self):
    """Push one changeset, sanity check all the data."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    start = time()
    push(u, self.clonerepo, dest=self.repodir)
    end = time()
    p = getPushesFromDB(self.repo)
    self.assertEqual(len(p), 1)
    self.assertEqual(len(p[0]['changes']), 1)
    self.assertEqual(p[0]['user'], getuser())
    # tough to assert exactly
    self.assert_(p[0]['date'] >= int(start))
    self.assert_(p[0]['date'] <= int(end))
    c = p[0]['changes'][0]
    tip = self.clonerepo.changectx('tip')
    self.assertEqual(c['rev'], tip.rev())
    self.assertEqual(c['node'], hex(tip.node()))

  def testTwoPushes(self):
    """Push two changesets in two pushes, sanity check all the data."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    push(u, self.clonerepo, dest=self.repodir)

    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 bug 23456")
    push(u, self.clonerepo, dest=self.repodir)

    pushes = getPushesFromDB(self.repo)
    self.assertEqual(len(pushes), 2)
    self.assert_(all(len(p['changes']) == 1 for p in pushes))
    self.assert_(all(p['user'] == getuser() for p in pushes))
    self.assert_(pushes[0]['date'] <= pushes[1]['date'])
    self.assert_(pushes[0]['changes'][0]['rev'] <= pushes[1]['changes'][0]['rev'])
    # check that all the node/rev pairs we recorded match what hg thinks
    self.assert_(all(self.clonerepo.changectx(c['node']).rev() == c['rev'] for p in pushes for c in p['changes']))

  def testTwoChangesOnePush(self):
    """Push two changesets in one push, sanity check all the data."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 bug 23456")
    start = time()
    push(u, self.clonerepo, dest=self.repodir)
    end = time()

    pushes = getPushesFromDB(self.repo)
    self.assertEqual(len(pushes), 1)
    p = pushes[0]
    self.assertEqual(len(p['changes']), 2)
    self.assertEqual(p['user'], getuser())
    self.assert_(p['date'] >= int(start))
    self.assert_(p['date'] <= int(end))
    self.assert_(p['changes'][0]['rev'] <= p['changes'][1]['rev'])
    # check that all the node/rev pairs we recorded match what hg thinks
    self.assert_(all(self.clonerepo.changectx(c['node']).rev() == c['rev'] for c in p['changes']))

  def testPushlogPermissions(self):
    """Check that the pushlog db is group writable after pushing."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    push(u, self.clonerepo, dest=self.repodir)

    st = os.stat(join(self.repodir, ".hg", "pushlog2.db"))
    self.assertEqual(st.st_mode & stat.S_IWGRP, stat.S_IWGRP)

  def testEmptyDB(self):
    """bug 466149 - Check that pushing to a db without a schema succeeds."""
    u = self.ui
    # empty the db file
    with open(join(self.repodir, ".hg", "pushlog2.db"), 'w') as f:
      pass
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    push(u, self.clonerepo, dest=self.repodir)

    p = getPushesFromDB(self.repo)
    self.assertEqual(len(p), 1)
    self.assertEqual(len(p[0]['changes']), 1)

  def testDBLocking(self):
    """bug 508863 - Lock the DB and try to push, check that the error doesn't suck so much."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    push(u, self.clonerepo, dest=self.repodir)

    # open the repo and insert something to lock it
    conn = sqlite.connect(join(self.repo.root, '.hg', 'pushlog2.db'))
    conn.execute("INSERT INTO pushlog (user, date) VALUES('user', 0)")

    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 bug 23456")
    sawError = False
    #TODO: would be nice if we could lower the timeout
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)
    conn.commit()
    # this one should succeed
    push(u, self.clonerepo, dest=self.repodir)
    conn.close()

class ClosureHookTestHelpers:
  """A mixin that provides a director class so we can intercept urlopen and
     change the result for our tests."""
  def setUp(self):
    # add a urllib OpenerDirector so we can intercept urlopen
    class MyDirector:
      expected = []
      opened = 0
      def open(self, url, data=None, timeout=None):
        expectedURL, sendData = self.expected.pop()
        """
        If this is ever changed so that more than one url are allowed, then
        the comm-central tests must be re-evaluated as they currently rely
        on it.
        """
        if expectedURL != url:
          raise Exception("Incorrect URL, got %s expected %s!" % (url, expectedURL))
        self.opened += 1
        return StringIO(sendData)
      def expect(self, url, data):
        """
        Indicate that the next url opened should be |url|, and should return
        |data| as its contents.
        """
        self.expected.append((url, data))
    self.director = MyDirector()
    urllib2.install_opener(self.director)

  def tearDown(self):
    urllib2.install_opener(urllib2.OpenerDirector())

  def redirect(self, url, data):
    self.director.expect(url, data)

class TestTreeClosureHook(ClosureHookTestHelpers, unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodirbase = mkdtemp(prefix="hg-test")
    #XXX: sucks, but tests can rename it if they'd like to test something else
    self.repodir = join(self.repodirbase, "mozilla-central")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "treeclosure.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    ClosureHookTestHelpers.setUp(self)

  def tearDown(self):
    shutil.rmtree(self.repodirbase)
    shutil.rmtree(self.clonedir)
    ClosureHookTestHelpers.tearDown(self)

  def testOpen(self):
    """Pushing to an OPEN tree should succeed."""
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                  '<span id="treestatus">OPEN</span><span id="extended-status">')

    # pushing something should now succeed
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testClosed(self):
    """Pushing to a CLOSED tree should fail."""
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">CLOSED</span><span id="extended-status">')
    # pushing something should now fail
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testClosedMagicWords(self):
    """
    Pushing to a CLOSED tree with 'CLOSED TREE' in the commit message
    should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">CLOSED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 CLOSED TREE")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testClosedMagicWordsTip(self):
    """
    Pushing multiple changesets to a CLOSED tree with 'CLOSED TREE'
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">CLOSED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 CLOSED TREE")

    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testApprovalRequired(self):
    """Pushing to an APPROVAL REQUIRED tree should fail."""
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">APPROVAL REQUIRED</span><span id="extended-status">')
    # pushing something should now fail
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testApprovalRequiredMagicWords(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">APPROVAL REQUIRED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 a=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

    # also check that approval of the form a1.2=foo works
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">APPROVAL REQUIRED</span><span id="extended-status">')
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 a1.2=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 2)

  def testApprovalRequiredMagicWordsTip(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/Firefox/status.html",
                         '<span id="treestatus">APPROVAL REQUIRED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    commit(u, self.clonerepo, message="checkin 2 a=someone")

    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

class TestTreeCommCentralClosureHook(ClosureHookTestHelpers, unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodirbase = mkdtemp(prefix="hg-test")
    #XXX: sucks, but tests can rename it if they'd like to test something else
    self.repodir = join(self.repodirbase, "comm-central")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "treeclosure_comm_central.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    ClosureHookTestHelpers.setUp(self)

  def tearDown(self):
    shutil.rmtree(self.repodirbase)
    shutil.rmtree(self.clonedir)
    ClosureHookTestHelpers.tearDown(self)

  def actualTestCCOpen(self, treeName, fileInfo):
    """Pushing to an OPEN CC tree should succeed."""
    # If this tests attempts to pull something that isn't treeName, then the
    # re-director should fail for us. Hence we know that the hook is only
    # pulling the predefined tree and nothing else.
    self.redirect("http://tinderbox.mozilla.org/" + treeName + "/status.html",
                         '<span id="tree-status">OPEN</span><span id="extended-status">')

    # pushing something should now succeed
    u = self.ui

    fileName = fileInfo.pop()
    fileLoc = self.clonedir
    for dir in fileInfo:
      fileLoc = join(fileLoc, dir)
      os.mkdir(fileLoc)

    fileLoc = join(fileLoc, fileName)

    appendFile(fileLoc, "checkin 1")
    add(u, self.clonerepo, fileLoc)
    commit(u, self.clonerepo, message="checkin 1")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

 
  def testCCOpenThunderbird(self):
    self.actualTestCCOpen("ThunderbirdTrunk", ["testfile"])

  def testCCOpenSeaMonkey(self):
    self.actualTestCCOpen("SeaMonkey", ["suite", "build", "test"])

  def testCCOpenCalendar1(self):
    self.actualTestCCOpen("CalendarTrunk", ["calendar", "app", "test"])

  def testCCOpenCalendar2(self):
    self.actualTestCCOpen("CalendarTrunk", ["other-licenses", "branding", "sunbird", "test"])

  def actualTestCCClosed(self, treeName, fileInfo):
    """Pushing to a CLOSED Thunderbird tree should fail."""
    # If this tests attempts to pull something that isn't treeName, then the
    # re-director should fail for us. Hence we know that the hook is only
    # pulling the predefined tree and nothing else.
    self.redirect("http://tinderbox.mozilla.org/" + treeName + "/status.html",
                         '<span id="tree-status">CLOSED</span><span id="extended-status">')

    # pushing something should now fail
    u = self.ui

    fileName = fileInfo.pop()
    fileLoc = self.clonedir
    for dir in fileInfo:
      fileLoc = join(fileLoc, dir)
      os.mkdir(fileLoc)

    fileLoc = join(fileLoc, fileName)

    appendFile(fileLoc, "checkin 1")
    add(u, self.clonerepo, fileLoc)
    commit(u, self.clonerepo, message="checkin 1")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testCCClosedThunderbird(self):
    self.actualTestCCClosed("ThunderbirdTrunk", ["testfile"])

  def testCCClosedSeaMonkey(self):
    self.actualTestCCClosed("SeaMonkey", ["suite", "build", "test"])

  def testCCClosedCalendar1(self):
    self.actualTestCCClosed("CalendarTrunk", ["calendar", "app", "test"])

  def testCCClosedCalendar2(self):
    self.actualTestCCClosed("CalendarTrunk", ["other-licenses", "branding", "sunbird", "test"])

  # In theory adding CLOSED TREE is the same code-path for all projects,
  # so just checking for one project
  def testCCClosedThunderbirdMagicWords(self):
    """
    Pushing to a CLOSED Thunderbird tree with 'CLOSED TREE' in the commit message
    should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">CLOSED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 CLOSED TREE")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  # In theory adding CLOSED TREE is the same code-path for all projects,
  # so just checking for one project
  def testCCClosedThunderbirdMagicWordsTip(self):
    """
    Pushing multiple changesets to a CLOSED Thunderbird tree with 'CLOSED TREE'
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">CLOSED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 CLOSED TREE")

    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testCCApprovalRequired(self):
    """Pushing to an APPROVAL REQUIRED tree should fail."""
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">APPROVAL REQUIRED</span><span id="extended-status">')
    # pushing something should now fail
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testCCApprovalRequiredMagicWords(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">APPROVAL REQUIRED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 a=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

    # also check that approval of the form a1.2=foo works
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">APPROVAL REQUIRED</span><span id="extended-status">')
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 a1.2=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 2)

  def testCCApprovalRequiredMagicWordsTip(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("http://tinderbox.mozilla.org/ThunderbirdTrunk/status.html",
                         '<span id="tree-status">APPROVAL REQUIRED</span><span id="extended-status">')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    commit(u, self.clonerepo, message="checkin 2 a=someone")

    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

class TestTryMandatoryHook(ClosureHookTestHelpers, unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-test")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "try_mandatory.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    ClosureHookTestHelpers.setUp(self)

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)
    ClosureHookTestHelpers.tearDown(self)

  def testWithoutTrySyntax(self):
    """Push one changeset, without using the try syntax should error."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testWithTrySyntax(self):
    """Push one changeset, with using the try syntax should succeed."""
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 try: -b do -p all")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)



if __name__ == '__main__':
  unittest.main()
