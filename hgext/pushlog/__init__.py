# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''Record pushes to Mercurial repositories.'''

import contextlib
import os
import sqlite3
import stat
import time
import weakref

testedwith = '3.0 3.1 3.2'

SCHEMA = [
    'CREATE TABLE IF NOT EXISTS changesets (pushid INTEGER, rev INTEGER, node text)',
    'CREATE TABLE IF NOT EXISTS pushlog (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date INTEGER)',
    'CREATE UNIQUE INDEX IF NOT EXISTS changeset_node ON changesets (node)',
    'CREATE UNIQUE INDEX IF NOT EXISTS changeset_rev ON changesets (rev)',
    'CREATE INDEX IF NOT EXISTS changeset_pushid ON changesets (pushid)',
    'CREATE INDEX IF NOT EXISTS pushlog_date ON pushlog (date)',
    'CREATE INDEX IF NOT EXISTS pushlog_user ON pushlog (user)',
]

class pushlog(object):
    '''An interface to pushlog data.'''

    def __init__(self, repo):
        '''Create an instance bound to a sqlite database in a path.'''
        # Use a weak ref to avoid cycle. This object's lifetime should be no
        # greater than the repo's.
        self.repo = weakref.proxy(repo)

    @contextlib.contextmanager
    def conn(self):
        path = self.repo.vfs.join('pushlog2.db')
        create = False
        if not os.path.exists(path):
            create = True

        conn = sqlite3.connect(path)
        if not create:
            res = conn.execute(
                "SELECT COUNT(*) FROM SQLITE_MASTER WHERE name='pushlog'")
            if res.fetchone()[0] != 1:
                create = True

        if create:
            for sql in SCHEMA:
                conn.execute(sql)
            conn.commit()
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IWGRP)

        try:
            yield conn
        finally:
            conn.close()

    def recordpush(self, nodes, user, when):
        '''Record a push into the pushlog.

        A push consists of a list of nodes, a username, and a time of the
        push.
        '''
        with self.conn() as c:
            res = c.execute('INSERT INTO pushlog (user, date) VALUES (?, ?)', (user, when))
            pushid = res.lastrowid
            for e in nodes:
                ctx = self.repo[e]
                rev = ctx.rev()
                node = ctx.hex()

                c.execute('INSERT INTO changesets (pushid, rev, node) '
                        'VALUES (?, ?, ?)', (pushid, rev, node))

            c.commit()

def pretxnchangegrouphook(ui, repo, node=None, source=None, **kwargs):
    # This hook is executed whenever changesets are introduced. We ignore
    # new changesets unless they come from a push. ``source`` can be
    # ``push`` for ssh or ``serve`` for HTTP pushes.
    #
    # This is arguably the wrong thing to do: designing a system to record
    # all changes to the store is the right thing to do. However, things are
    # like this for backwards compatibility with the original intent of
    # pushlog.
    if source not in ('push', 'serve'):
        ui.status('(not updating pushlog since changesets come from %s)\n' % source)
        return 0

    ui.write('Trying to insert into pushlog.\n')
    ui.write('Please do not interrupt...\n')
    try:
        t = int(time.time())
        revs = range(repo[node].rev(), len(repo))
        repo.pushlog.recordpush(revs, os.environ['USER'], t)
        ui.write('Inserted into the pushlog db successfully.\n')
        return 0
    except Exception:
        ui.write('Error inserting into pushlog. Please retry your push.\n')

    return 1

def reposetup(ui, repo):
    if not repo.local():
        return

    ui.setconfig('hooks', 'pretxnchangegroup.pushlog', pretxnchangegrouphook, 'pushlog')

    class pushlogrepo(repo.__class__):
        @property
        def pushlog(self):
            if not hasattr(self, '_pushlog'):
                self._pushlog = pushlog(self)

            return self._pushlog

    repo.__class__ = pushlogrepo
