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

if __name__ == '__main__':
  unittest.main()
