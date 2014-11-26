# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''Record pushes to Mercurial repositories.'''

import contextlib
import os
import sqlite3
import stat
import time
import weakref

from mercurial import (
    exchange,
    extensions,
    wireproto,
)

from mercurial.error import Abort
from mercurial.node import bin, hex

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

# Wraps capabilities wireproto command to advertise pushlog availability.
def capabilities(orig, repo, proto):
    caps = orig(repo, proto)
    caps.append('pushlog')
    return caps

@wireproto.wireprotocommand('pushlog', 'firstpush')
def pushlogwireproto(repo, proto, firstpush):
    """Return pushlog data from a start offset.

    The response is a series of lines.

    The first line starts with "0" or "1". This indicates success. If the line
    starts with "0", an error message should follow. e.g.
    ``0 exception when accessing sqlite``.

    All subsequent lines describe individual pushes. The format of these lines
    is:

      <push ID> <author> <when> <node0> [<node1> [<node2> ...]]

    That is:

      * An integer ID for the push.
      * A string of the user (SSH username) who performed the push
      * Integer seconds since UNIX epoch when this push was performed
      * A list of 40 byte hex changesets included in the push, in revset order
    """
    lines = ['1']

    try:
        firstpush = int(firstpush)

        for pushid, who, when, nodes in repo.pushlog.pushes():
            if pushid < firstpush:
                continue

            lines.append('%d %s %d %s' % (pushid, who, when, ' '.join(nodes)))

        return '\n'.join(lines)
    except Exception as e:
        return '\n'.join(['0', str(e)])

def exchangepullpushlog(orig, pullop):
    """This is called during pull to fetch pushlog data."""
    # check stepsdone for future compatibility with bundle2 pushlog exchange.
    if 'pushlog' in pullop.stepsdone or not pullop.remote.capable('pushlog'):
        return orig(pullop)

    repo = pullop.repo
    fetchfrom = repo.pushlog.lastpushid() + 1
    lines = pullop.remote._call('pushlog', firstpush=str(fetchfrom))
    lines = iter(lines.splitlines())

    statusline = lines.next()
    if statusline[0] == '0':
        raise Abort('error fetching pushlog: %s' % lines[1])
    elif statusline != '1':
        raise Abort('error fetching pushlog: unexpected response: %s\n' %
            statusline)

    pushes = []
    for line in lines:
        pushid, who, when, nodes = line.split(' ', 3)
        nodes = [bin(n) for n in nodes.split()]
        pushes.append((int(pushid), who, int(when), nodes))

    repo.pushlog.recordpushes(pushes)
    repo.ui.status('added %d pushes\n' % len(pushes))

    return orig(pullop)

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

    def recordpushes(self, pushes):
        """Record multiple pushes.

        This is effectively a version of ``recordpush()`` that accepts multiple
        pushes.

        It accepts in iterable of tuples:

          (pushid, user, time, nodes)

        Where ``nodes`` is an iterable of changeset identifiers (both bin and
        hex forms are accepted).
        """
        with self.conn() as c:
            for pushid, user, when, nodes in pushes:
                c.execute('INSERT INTO pushlog (id, user, date) VALUES (?, ?, ?)',
                    (pushid, user, when))
                for n in nodes:
                    ctx = self.repo[n]
                    rev = ctx.rev()
                    node = ctx.hex()

                    c.execute('INSERT INTO changesets (pushid, rev, node) '
                        'VALUES (?, ?, ?)', (pushid, rev, node))

            c.commit()

    def lastpushid(self):
        """Obtain the integer pushid of the last known push."""
        with self.conn() as c:
            res = c.execute('SELECT id from pushlog ORDER BY id DESC').fetchone()
            if not res:
                return 0
            return res[0]

    def pushes(self):
        """Return information about pushes to this repository.

        This is a generator of tuples describing each push. Each tuple has the
        form:

            (pushid, who, when, [nodes])

        Nodes are returned in their 40 byte hex form.
        """
        with self.conn() as c:
            res = c.execute('SELECT id, user, date, rev, node from pushlog '
                    'LEFT JOIN changesets ON id=pushid '
                    'ORDER BY id, rev ASC')

            lastid = None
            current = None
            for pushid, who, when, rev, node in res:
                who = who.encode('utf-8')
                node = node.encode('ascii')
                if pushid != lastid:
                    if current:
                        yield current
                    lastid = pushid
                    current = (pushid, who, when, [node])
                else:
                    current[3].append(node)

            if current:
                yield current

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

def extsetup(ui):
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)
    extensions.wrapfunction(exchange.pulloperation, 'closetransaction',
        exchangepullpushlog)

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
