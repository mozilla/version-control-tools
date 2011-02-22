#!/usr/bin/env python

# Copyright (C) 2010 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# This script implements a Mercurial hook to log the date and time when
# changesets are pushed into a repository, and the user that pushed them.
#
# run `python setup.py install` to install the module in the proper place,
# and then modify the repository's hgrc as per example-hgrc.

from mercurial import demandimport

demandimport.disable()
try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
demandimport.enable()

import time
import os
import os.path
import stat
from mercurial.node import hex

def createpushdb(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS changesets (pushid INTEGER, rev INTEGER, node text)")
    conn.execute("CREATE TABLE IF NOT EXISTS pushlog (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date INTEGER)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS changeset_node ON changesets (node)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS changeset_rev ON changesets (rev)")
    conn.execute("CREATE INDEX IF NOT EXISTS changeset_pushid ON changesets (pushid)")
    conn.execute("CREATE INDEX IF NOT EXISTS pushlog_date ON pushlog (date)")
    conn.execute("CREATE INDEX IF NOT EXISTS pushlog_user ON pushlog (user)")
    conn.commit()

def schemaexists(conn):
    return 1 == conn.execute("SELECT COUNT(*) FROM SQLITE_MASTER WHERE name='pushlog'").fetchone()[0]

def log(ui, repo, node, **kwargs):
    pushdb = os.path.join(repo.path, 'pushlog2.db')
    createdb = False
    if not os.path.exists(pushdb):
        createdb = True
    conn = sqlite.connect(pushdb)
    if not createdb and not schemaexists(conn):
        createdb = True
    if createdb:
        createpushdb(conn)
        st = os.stat(pushdb)
        os.chmod(pushdb, st.st_mode | stat.S_IWGRP)
    t = int(time.time())
    retval = 1
    print "Trying to insert into pushlog."
    print "Please do not interrupt..."
    try:
        res = conn.execute("INSERT INTO pushlog (user, date) values(?,?)",
                           (os.environ['USER'], t))
        pushid = res.lastrowid
        # all changesets from node to 'tip' inclusive are part of this push
        rev = repo.changectx(node).rev()
        tip = repo.changectx('tip').rev()
        for i in range(rev, tip+1):
            ctx = repo.changectx(i)
            conn.execute("INSERT INTO changesets (pushid,rev,node) VALUES(?,?,?)",
                         (pushid, ctx.rev(), hex(ctx.node())))
        conn.commit()
        retval = 0
        print "Inserted into the pushlog db successfully."
    except sqlite.OperationalError:
        print "Pushlog database is locked. Please retry your push."
    conn.close()
    return retval
