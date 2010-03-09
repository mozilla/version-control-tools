#!/usr/bin/env python

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

def addHook(repodir):
  with open(join(repodir, '.hg', 'hgrc'), 'w') as f:
    f.write("""[hooks]
pretxnchangegroup.z_linearhistory = python:mozhghooks.pushlog.log
""")

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

class TestHook(unittest.TestCase):
  def setUp(self):
    self.ui = ui.ui()
    self.ui.quiet = True
    self.ui.verbose = False
    self.repodir = mkdtemp(prefix="hg-test")
    init(self.ui, dest=self.repodir)
    addHook(self.repodir)
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
    try:
      push(u, self.clonerepo, dest=self.repodir)
    except util.Abort:
      sawError = True
    self.assert_(sawError, "Push was aborted due to db being locked.")
    conn.commit()
    # this one should succeed
    push(u, self.clonerepo, dest=self.repodir)
    conn.close()

if __name__ == '__main__':
  unittest.main()
