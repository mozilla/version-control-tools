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

from datetime import datetime
import os
import os.path

def createpushdb(conn):
    conn.execute("CREATE TABLE pushlog (node text, user text, date text)")
    conn.execute("CREATE INDEX pushlog_date ON pushlog (date)")
    conn.execute("CREATE INDEX pushlog_user ON pushlog (user)")
    conn.commit()

def log(ui, repo, node, **kwargs):
    pushdb = os.path.join(repo.path, 'pushlog.db')
    createdb = False
    if not os.path.exists(pushdb):
        createdb = True
    conn = sqlite.connect(pushdb)
    if createdb:
        createpushdb(conn)
    d = datetime.utcnow().replace(microsecond=0)
    conn.execute("INSERT INTO pushlog (node, user, date) values(?,?,?)",
                 (node, os.environ['USER'], d.isoformat()+"Z"))
    conn.commit()
