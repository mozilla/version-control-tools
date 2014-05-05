#!/usr/bin/env python

from __future__ import with_statement
import unittest
from mercurial import ui, hg, commands, util
from mercurial.commands import add, clone, commit, init, push, rename, remove, update, merge
from mercurial.node import hex, short
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
  try:
    os.makedirs(os.path.dirname(filename))
  except:
    pass
  with open(filename, 'a') as f:
    f.write(content)

def removeFromFile(filename, content):
  try:
    os.makedirs(os.path.dirname(filename))
  except:
    pass
  newlines = []
  with open(filename, 'r') as f:
    lines = f.readlines()
    for line in lines:
        if line != content:
            newlines.append(line)
  with open(filename, 'a') as f:
    f.write(''.join(newlines))

def editFile(filename, original, updated):
  try:
    os.makedirs(os.path.dirname(filename))
  except:
    pass
  newlines = []
  with open(filename, 'r') as f:
    lines = f.readlines()
    for line in lines:
        if line == original:
            newlines.append(updated)
        else:
            newlines.append(line)
  with open(filename, 'a') as f:
    f.write(''.join(newlines))

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
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "open", "reason": null}')

    # pushing something should now succeed
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

  def testClosed(self):
    """Pushing to a CLOSED tree should fail."""
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "closed", "reason": "splines won\'t reticulate"}')
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
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "closed", "reason": "too many widgets"}')
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
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "closed", "reason": "the end of the world as we know it"}')
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
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "approval required", "reason": "be verrrry careful"}')
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
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "approval required", "reason": "trees are fragile"}')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 a=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

    # also check that approval of the form a1.2=foo works
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "approval required", "reason": "like they\'re made of glass"}')
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 a1.2=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 2)

  def testApprovalRequiredMagicWordsTip(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("https://treestatus.mozilla.org/mozilla-central?format=json",
                '{"status": "approval required", "reason": "stained glass"}')
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
    self.redirect("https://treestatus.mozilla.org/comm-central-" + treeName.lower() + "?format=json",
                  '{"status": "open", "reason": null}')

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
    self.actualTestCCOpen("Thunderbird", ["testfile"])

  def testCCOpenSeaMonkey(self):
    self.actualTestCCOpen("SeaMonkey", ["suite", "build", "test"])

  def testCCOpenCalendar(self):
    # Calendar is now built alongside Thunderbird
    self.actualTestCCOpen("Thunderbird", ["calendar", "app", "test"])

  def actualTestCCClosed(self, treeName, fileInfo):
    """Pushing to a CLOSED CC tree should fail."""
    # If this tests attempts to pull something that isn't treeName, then the
    # re-director should fail for us. Hence we know that the hook is only
    # pulling the predefined tree and nothing else.
    self.redirect("https://treestatus.mozilla.org/comm-central-" + treeName.lower() + "?format=json",
                  '{"status": "closed", "reason": null}')

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
    self.actualTestCCClosed("Thunderbird", ["testfile"])

  def testCCClosedSeaMonkey(self):
    self.actualTestCCClosed("SeaMonkey", ["suite", "build", "test"])

  def testCCClosedCalendar(self):
    # Calendar is now built alongside Thunderbird
    self.actualTestCCClosed("Thunderbird", ["calendar", "app", "test"])

  # In theory adding CLOSED TREE is the same code-path for all projects,
  # so just checking for one project
  def testCCClosedThunderbirdMagicWords(self):
    """
    Pushing to a CLOSED Thunderbird tree with 'CLOSED TREE' in the commit message
    should succeed.
    """
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "closed", "reason": null}')
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
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "closed", "reason": null}')
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
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "approval required", "reason": null}')
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
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "approval required", "reason": null}')
    u = self.ui
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(u, self.clonerepo, join(self.clonedir, "testfile"))
    commit(u, self.clonerepo, message="checkin 1 a=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 1)

    # also check that approval of the form a1.2=foo works
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "approval required", "reason": null}')
    appendFile(join(self.clonedir, "testfile"), "checkin 2")
    commit(u, self.clonerepo, message="checkin 2 a1.2=someone")
    push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(self.director.opened, 2)

  def testCCApprovalRequiredMagicWordsTip(self):
    """
    Pushing to an APPROVAL REQUIRED tree with a=foo
    in the commit message of the tip changeset should succeed.
    """
    self.redirect("https://treestatus.mozilla.org/comm-central-thunderbird?format=json",
                  '{"status": "approval required", "reason": null}')
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

class TestCommitMessageHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-TestCommitMessageHook")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "commit-message.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    
  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)
    
  def testWithBug(self):
    """ Every test should have bug # like "Bug 111", "Bug #111" or "b=111". """

    ui = self.ui
    messages = [
      "Bug 603517 - Enable mochitest to optionally run in loops without restarting the browser r=ctalbert",
      "Bug #123456 - add test",
      "b=630117, rename typed array slice() -> subset(); r=jwalden, a=block"
      "ARM assembler tweaks. (b=588021, r=cdleary)"
    ]

    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    for message in messages:
      commit(ui, self.clonerepo, message=message)

    result = push(ui, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testBackout(self):
    """ Test different ways of spelling backout (and revert). """

    ui = self.ui
    messages = [
      "Backed out changeset 593d94e9492e",
      "Backout changesets 9e4ab3907b29, 3abc0dbbf710 due to m-oth permaorange",
      "Backout of 35a679df430b due to bustage",
      "backout 68941:5b8ade677818", # including the local numeric ID is silly but harmless
      
      # we do not have a lot of reverts "hg log | grep revert" without a bug #
      "Revert to changeset a87ee7550f6a due to incomplete backout" 
    ]
    
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    for message in messages:
      commit(ui, self.clonerepo, message=message)
    result = push(ui, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)
    
  def testSpecial(self):
    """ Test some special stuff like "no bug", "add tag" or "update nanojit-import-rev stamp". """

    ui = self.ui
    messages = [
      "Added tag AURORA_BASE_20110412 for changeset a95d42642281",
      "Fix typo in comment within nsFrame.cpp (no bug) rs=dbaron DONTBUILD",
      "Fix ARM assert (no bug, r=cdleary).",
      "Backout 3b59c196aaf9 - no bug # in commit message"
    ]

    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    for message in messages:
      commit(ui, self.clonerepo, message=message)
    result = push(ui, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  bad = [
    "Mass revert m-i to the last known good state",
    "update revision of Add-on SDK tests to latest tip; test-only",
    "Fix stupid bug in foo::bar()",
    "First line does not have a bug number\n\nbug 123456",
    "imported patch phishingfixes",
    "imported patch 441197-1",
    "Back out Dao's push because of build bustage",
    "Bump mozilla-central version numbers for the next release on a CLOSED TREE.",
    "Bump Sync version to 1.9.0. r=me",
    "checkin 1 try: -b do -p all"
  ]

  def testShouldFail(self):
    """ Some commit messages that should explicitly not pass anymore. """

    ui = self.ui
    
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    
    for message in self.bad:
      appendFile(join(self.clonedir, "testfile"), "checkin 1")
      commit(ui, self.clonerepo, message=message)
      print message
      self.assertRaises(util.Abort, push, ui, self.clonerepo, dest=self.repodir)
      
  def testIgnore(self):
    """ Test that IGNORE BAD COMMIT MESSAGES works """
    ui = self.ui
    
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    
    for message in self.bad:
      appendFile(join(self.clonedir, "testfile"), "checkin 1")
      commit(ui, self.clonerepo, message=message)
    
    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    commit(ui, self.clonerepo, message="IGNORE BAD COMMIT MESSAGES")

    result = push(ui, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

class TestCaseOnlyRenameHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-TestCaseOnlyRenameHook")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "prevent_case_only_renames.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)

  def testTipShouldFail(self):
    """ Test that a case-only rename in tip should fail. """

    ui = self.ui

    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    commit(ui, self.clonerepo, message="checkin 1")
    rename(ui, self.clonerepo,
           join(self.clonedir, "testfile"),
           join(self.clonedir, "TESTFILE"));
    commit(ui, self.clonerepo, message="checkin 2")
    self.assertRaises(util.Abort, push, ui, self.clonerepo, dest=self.repodir)

  def testTipDirRenameShouldFail(self):
    """ Test that a case-only directory rename in tip should fail. """

    ui = self.ui

    appendFile(join(self.clonedir, "testdir/testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testdir/testfile"))
    commit(ui, self.clonerepo, message="checkin 1")
    rename(ui, self.clonerepo,
           join(self.clonedir, "testdir/testfile"),
           join(self.clonedir, "TESTDIR/testfile"));
    commit(ui, self.clonerepo, message="checkin 2")
    self.assertRaises(util.Abort, push, ui, self.clonerepo, dest=self.repodir)

  def testPreviousShouldFail(self):
    """ Test that a case-only rename that's not tip should fail. """

    ui = self.ui

    appendFile(join(self.clonedir, "testfile"), "checkin 1")
    add(ui, self.clonerepo, join(self.clonedir, "testfile"))
    commit(ui, self.clonerepo, message="checkin 1")

    rename(ui, self.clonerepo,
           join(self.clonedir, "testfile"),
           join(self.clonedir, "TESTFILE"));
    commit(ui, self.clonerepo, message="checkin 2")

    appendFile(join(self.clonedir, "TESTFILE"), "checkin 3")
    commit(ui, self.clonerepo, message="checkin 3")

    self.assertRaises(util.Abort, push, ui, self.clonerepo, dest=self.repodir)

class TestPreventUUIDHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-TestPreventUUIDHook")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "prevent_uuid_changes.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    # Create a pre-existing repo with a file that contains UUID
    appendFile(join(self.clonedir, "original.idl"), "uuid(abc123)")
    add(self.ui, self.clonerepo, join(self.clonedir, "original.idl"))
    commit(self.ui, self.clonerepo, message="original repo commit ba=me")
    push(self.ui, self.clonerepo, dest=self.repodir)
    print "===== In method", self._testMethodName, " ======="

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)

  def testUUIDEditExistingShouldFail(self):
    """ Test that editing .idl file with 'uuid(' and no 'ba=' should fail  """
    u = self.ui
    editFile(join(self.clonedir, "original.idl"), "uuid(abc123)", "uuid(def456)")
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testUUIDEditExistingShouldPass(self):
    """ Test that editing .idl file with 'uuid(' with ba=... should pass """
    u = self.ui
    editFile(join(self.clonedir, "original.idl"), "uuid(abc123)", "uuid(def456)")
    commit(u, self.clonerepo, message="checkin 1 bug 12345 ba=me")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testUUIDMultiplePushShouldFail(self):
    """ Test that adding .idl file with uuid with other files and no 'ba=' should fail  """
    u = self.ui
    appendFile(join(self.clonedir, "testfile1.idl"), "uuid(something here)")
    add(u, self.clonerepo, join(self.clonedir, "testfile1.idl"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    appendFile(join(self.clonedir, "testfile2.txt"), "checkin2")
    add(u, self.clonerepo, join(self.clonedir, "testfile2.txt"))
    commit(u, self.clonerepo, message="checkin 2 bug 12345")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testUUIDMultiplePushShouldPass(self):
    """ Test that changeset with 'uuid(' change in .idl should pass if 'ba=...' is in the push comment """
    u = self.ui
    appendFile(join(self.clonedir, "testfile3.idl"), "uuid(something here)")
    add(u, self.clonerepo, join(self.clonedir, "testfile3.idl"))
    commit(u, self.clonerepo, message="checkin 3 bug 12345")
    appendFile(join(self.clonedir, "testfile2.txt"), "checkin2")
    add(u, self.clonerepo, join(self.clonedir, "testfile2.txt"))
    commit(u, self.clonerepo, message="checkin 2 bug 12345 ba=approver")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testUUIDNonIDLShouldPass(self):
    """ Test that changeset with 'uuid(' change in a file not ending in .idl should pass """
    u = self.ui
    appendFile(join(self.clonedir, "testfile1.txt"), "uuid(something here)")
    add(u, self.clonerepo, join(self.clonedir, "testfile1.txt"))
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testUUIDRemoveUUIDNoApprovalShouldFail(self):
    """ Test that changeset with 'uuid(' removed from file ending in .idl should fail """
    u = self.ui
    appendFile(join(self.clonedir, "original.idl"), "line of text")
    removeFromFile(join(self.clonedir, "original.idl"), "uuid(abc123)")
    commit(u, self.clonerepo, message="checkin removed uuid bug 12345")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testUUIDRemoveUUIDWithApprovalShouldPass(self):
    """ Test that changeset with 'uuid(' removed from file ending in .idl should pass with ba=... """
    u = self.ui
    appendFile(join(self.clonedir, "original.idl"), "line of text")
    removeFromFile(join(self.clonedir, "original.idl"), "uuid(abc123)")
    commit(u, self.clonerepo, message="checkin removed uuid bug 12345 ba=me")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testUUIDDeletedIDLApproveShouldPass(self):
    """ Test that changeset with .idl file removed should pass with ba= approval """
    u = self.ui
    remove(u, self.clonerepo, join(self.clonedir, "original.idl"))
    commit(u, self.clonerepo, message="checkin 2 removed idl file ba=approver")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testUUIDDeletedIDLNoApproveShouldFail(self):
    """ Test that changeset with .idl file removed should fail without approval"""
    u = self.ui
    remove(u, self.clonerepo, join(self.clonedir, "original.idl"))
    commit(u, self.clonerepo, message="checkin 2 removed idl file ")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

class TestPreventWebIDLHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-TestPreventWebIDLHook")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir, "prevent_webidl_changes.hook")
    self.repo = hg.repository(self.ui, self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(self.ui, self.repo, self.clonedir)
    self.clonerepo = hg.repository(self.ui, self.clonedir)
    # Create a pre-existing repo with a file that contains UUID
    appendFile(join(self.clonedir, "original.webidl"), "interface Foo{};")
    add(self.ui, self.clonerepo, join(self.clonedir, "original.webidl"))
    appendFile(join(self.clonedir, "dummy"), "foo")
    add(self.ui, self.clonerepo, join(self.clonedir, "dummy"))
    commit(self.ui, self.clonerepo, message="original repo commit r=jst")
    push(self.ui, self.clonerepo, dest=self.repodir)

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)

  def testWebIDLEditWithoutReviewShouldFail(self):
    """ Test that editing .webidl file without review should fail """
    u = self.ui
    editFile(join(self.clonedir, "original.webidl"), "interface Foo{};", "interface Bar{};")
    commit(u, self.clonerepo, message="checkin 1 bug 12345")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testWebIDLEditWithoutProperReviewShouldFail(self):
    """ Test that editing .webidl file without proper DOM peer review should fail """
    u = self.ui
    editFile(join(self.clonedir, "original.webidl"), "interface Foo{};", "interface Bar{};")
    commit(u, self.clonerepo, message="checkin 1 bug 12345; r=foobar")
    self.assertRaises(util.Abort, push, u, self.clonerepo, dest=self.repodir)

  def testWebIDLEditWithProperReviewShouldPass(self):
    """ Test that editing .webidl file with proper DOM peer review should pass """
    u = self.ui
    editFile(join(self.clonedir, "original.webidl"), "interface Foo{};", "interface Bar{};")
    commit(u, self.clonerepo, message="checkin 1 bug 12345; r=foobar,jst")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testWebIDLEditWithProperReviewDuringMergeShouldPass(self):
    """ Test that editing .webidl file with proper DOM peer review should pass """
    u = self.ui
    parentrev = short(self.clonerepo.changectx('tip').node())
    editFile(join(self.clonedir, "original.webidl"), "interface Foo{};", "interface Bar{};")
    commit(u, self.clonerepo, message="checkin 1 bug 12345; r=foobar,jst")
    update(u, self.clonerepo, rev=parentrev)
    editFile(join(self.clonedir, "dummy"), "foo", "bar")
    commit(u, self.clonerepo, message="dummy")
    merge(u, self.clonerepo)
    commit(u, self.clonerepo, message="merge")
    result = push(u, self.clonerepo, dest=self.repodir)
    self.assertEqual(result, 0)

  def testWebIDLEditsInBackoutsWithoutProperReviewShouldPass(self):
    """ Test that editing .webidl file without proper DOM peer review in backouts should pass """
    u = self.ui
    # Copied from testBackout above.
    messages = [
      "Backed out changeset 593d94e9492e",
      "Backout changesets 9e4ab3907b29, 3abc0dbbf710 due to m-oth permaorange",
      "Backout of 35a679df430b due to bustage",
      "backout 68941:5b8ade677818", # including the local numeric ID is silly but harmless
      # we do not have a lot of reverts "hg log | grep revert" without a bug #
      "Revert to changeset a87ee7550f6a due to incomplete backout" 
    ]
    for message in messages:
      name = "new%d.webidl" % len(message)
      appendFile(join(self.clonedir, name), "interface Test{};")
      add(u, self.clonerepo, join(self.clonedir, name))
      commit(u, self.clonerepo, message=message)
      result = push(u, self.clonerepo, dest=self.repodir)
      self.assertEqual(result, 0)

if __name__ == '__main__':
  unittest.main()
