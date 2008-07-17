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
    conn.execute("CREATE INDEX IF NOT EXISTS pushlog_date ON pushlog (date)")
    conn.execute("CREATE INDEX IF NOT EXISTS pushlog_user ON pushlog (user)")
    conn.commit()

def log(ui, repo, node, **kwargs):
    pushdb = os.path.join(repo.path, 'pushlog2.db')
    createdb = False
    if not os.path.exists(pushdb):
        createdb = True
    conn = sqlite.connect(pushdb)
    if createdb:
        createpushdb(conn)
        st = os.stat(pushdb)
        os.chmod(pushdb, st.st_mode | stat.S_IWGRP)
    t = int(time.time())
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
