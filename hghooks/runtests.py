#!/usr/bin/env python

import unittest
from mercurial import ui, hg, commands
from mercurial.commands import add, clone, commit, init, push
from mercurial.node import hex
from tempfile import mkdtemp
import shutil
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
    pushes[-1]['changes'].append({'rev':row[3], 'node':row[4]})
  return pushes

class TestHook(unittest.TestCase):
  def setUp(self):
    self.repodir = mkdtemp(prefix="hg-test")
    init(ui.ui(), dest=self.repodir)
    addHook(self.repodir)
    self.repo = hg.repository(ui.ui(), self.repodir)
    self.clonedir = mkdtemp(prefix="hg-test")
    clone(ui.ui(), self.repo, self.clonedir)
    self.clonerepo = hg.repository(ui.ui(), self.clonedir)

  def tearDown(self):
    shutil.rmtree(self.repodir)
    shutil.rmtree(self.clonedir)

  def testBasic(self):
    """Push one changeset, sanity check all the data."""
    u = ui.ui()
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

if __name__ == '__main__':
  unittest.main()
