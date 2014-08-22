#!/usr/bin/env python

from __future__ import with_statement
import unittest
from mercurial import ui, hg, commands, util
from mercurial.commands import add, clone, commit, init, push, rename, remove, update, merge
from mercurial.node import hex, short
from tempfile import mkdtemp, mkstemp
import shutil
import os, stat
from os.path import join, exists
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

if __name__ == '__main__':
  unittest.main()
