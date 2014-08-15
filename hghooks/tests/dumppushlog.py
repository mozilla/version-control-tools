#!/usr/bin/env python

# Script to dump the contents of the pushlog db for a repo.

import os
import sqlite3
import sys

repo = sys.argv[1]
dbpath = os.path.join(repo, '.hg', 'pushlog2.db')

if not os.path.exists(dbpath):
    print('pushlog database does not exist: %s' % dbpath)
    sys.exit(1)

conn = sqlite3.connect(dbpath)
res = conn.execute('SELECT id, user, date, rev, node FROM pushlog '
    'INNER JOIN changesets on pushlog.id = changesets.pushid ORDER BY id')

lastdate = None
for pid, user, date, rev, node in res.fetchall():
    if lastdate:
        assert date >= lastdate

    lastdate = date

    print('ID: %d; user: %s; Date: %s; Rev: %d; Node: %s' % (
        pid, user, date, rev, node))
