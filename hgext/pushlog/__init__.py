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
    cmdutil,
    encoding,
    exchange,
    extensions,
    revset,
    util,
    wireproto,
)

from mercurial.error import (
    Abort,
    RepoLookupError,
)
from mercurial.node import bin, hex

testedwith = '3.2'

cmdtable = {}
command = cmdutil.command(cmdtable)

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

        for pushid, who, when, nodes in repo.pushlog.pushes(startid=firstpush):
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
        raise Abort('remote error fetching pushlog: %s' % lines.next())
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

    def _getconn(self, readonly=False):
        """Get a SQLite connection to the pushlog.

        In normal operation, this will return a ``sqlite3.Connection``.
        If the database does not exist, it will be created. If the database
        schema is not present or up to date, it will be updated. An error will
        be raised if any of this could not be performed.

        If ``readonly`` is truthy, ``None`` will be returned if the database
        file does not exist. This gives read-only consumers the opportunity to
        short-circuit if no data is available.
        """
        path = self.repo.vfs.join('pushlog2.db')
        create = False
        if not os.path.exists(path):
            if readonly:
                return None

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

        return conn

    @contextlib.contextmanager
    def conn(self, readonly=False):
        conn = self._getconn(readonly=readonly)
        try:
            yield conn
        finally:
            if conn:
                conn.close()

    def recordpush(self, nodes, user, when):
        '''Record a push into the pushlog.

        A push consists of a list of nodes, a username, and a time of the
        push.

        This function assumes it is running in the context of a transaction.
        There are valid scenarios where this may not hold true. However, we
        don't have a need to support them, so we error in these scenarios.
        '''
        if not isinstance(user, str):
            raise TypeError('Expected a str user. Got %s' % str(type(user)))

        # We want invalid usernames to fail insertion. This will raise
        # UnicodeDecodeError.
        user.decode('utf-8', 'strict')

        # WARNING low-level hacks applied.
        #
        # The active transaction object provides various instance-specific internal
        # callbacks. When we run, the transaction object comes from
        # localrepository.transaction(). The assert statements check our
        # assumptions for how that code works, namely that
        # localrepository.transaction() *always* defines these callbacks.
        #
        # The code here essentially monkeypatches the "finish" and "abort"
        # callbacks on the transaction to commit and close the database.
        #
        # If the database is closed without a commit(), the active transaction
        # (our inserts) will be rolled back.
        tr = self.repo._transref()
        assert tr.onabort is None
        assert tr.after

        c = self._getconn()
        oldafter = tr.after

        def abort():
            c.close()
            self.repo.ui.warn('rolling back pushlog\n')

        def commit():
            oldafter()
            c.commit()
            c.close()

        tr.onabort = abort
        tr.after = commit

        # Now that the hooks are installed, any exceptions will result in db
        # close via abort().
        res = c.execute('INSERT INTO pushlog (user, date) VALUES (?, ?)', (user, when))
        pushid = res.lastrowid
        for e in nodes:
            ctx = self.repo[e]
            rev = ctx.rev()
            node = ctx.hex()

            c.execute('INSERT INTO changesets (pushid, rev, node) '
                    'VALUES (?, ?, ?)', (pushid, rev, node))

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
                if not isinstance(user, str):
                    raise TypeError('Expected a str user. Got %s' % str(type(user)))

                user.decode('utf-8', 'strict')

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

    def pushes(self, startid=1):
        """Return information about pushes to this repository.

        This is a generator of tuples describing each push. Each tuple has the
        form:

            (pushid, who, when, [nodes])

        Nodes are returned in their 40 byte hex form.

        ``startid`` is the numeric pushid to start returning values from. Value
        is inclusive.
        """
        with self.conn(readonly=True) as c:
            if not c:
                return

            res = c.execute('SELECT id, user, date, rev, node from pushlog '
                    'LEFT JOIN changesets ON id=pushid '
                    'WHERE id >= ? '
                    'ORDER BY id, rev ASC', (startid,))

            lastid = None
            current = None
            for pushid, who, when, rev, node in res:
                who = who.encode('utf-8')

                # node could be None if no nodes associated with push.
                if node:
                    node = node.encode('ascii')
                if pushid != lastid:
                    if current:
                        yield current
                    lastid = pushid
                    current = (pushid, who, when, [])
                    if node:
                        current[3].append(node)
                else:
                    current[3].append(node)

            if current:
                yield current

    def verify(self):
        # Attempt to create database (since .pushes below won't).
        with self.conn():
            pass

        repo = self.repo
        ui = self.repo.ui

        ret = 0
        seennodes = set()
        pushcount = 0
        for pushcount, (pushid, who, when, nodes) in enumerate(self.pushes(), 1):
            if not nodes:
                ui.warn('pushlog entry has no nodes: #%s\n' % pushid)
                continue

            for node in nodes:
                try:
                    repo[node]
                except RepoLookupError:
                    ui.warn('changeset in pushlog entry #%s does not exist: %s\n' %
                        (pushid, node))
                    ret = 1

                seennodes.add(bin(node))

        for rev in repo:
            ctx = repo[rev]
            if ctx.node() not in seennodes:
                ui.warn('changeset does not exist in pushlog: %s\n' % ctx.hex())
                ret = 1

        if ret:
            ui.status('pushlog has errors\n')
        else:
            ui.status('pushlog contains all %d changesets across %d pushes\n' %
                (len(seennodes), pushcount))

        return ret

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
    try:
        t = int(time.time())
        revs = range(repo[node].rev(), len(repo))
        repo.pushlog.recordpush(revs, os.environ['USER'], t)
        ui.write('Inserted into the pushlog db successfully.\n')
        return 0
    except Exception:
        ui.write('Error inserting into pushlog. Please retry your push.\n')

    return 1

def revset_pushhead(repo, subset, x):
    """``pushhead()``
    Changesets that were heads when they were pushed.

    A push head is a changeset that was a head at the time it was pushed.
    """
    revset.getargs(x, 0, 0, 'pushhead takes no arguments')

    # Iterating over all pushlog data is unfortunate, as there is overhead
    # involved. However, this is less overhead than issuing a SQL query for
    # every changeset, especially on large repositories. There is room to make
    # this optimal by batching SQL, but that adds complexity. For now,
    # simplicity wins.
    def getrevs():
        for pushid, who, when, nodes in repo.pushlog.pushes():
            yield repo[nodes[-1]].rev()

    return subset & revset.generatorset(getrevs())

def revset_pushdate(repo, subset, x):
    """``pushdate(interval)``
    Changesets that were pushed within the interval, see :hg:`help dates`.
    """
    l = revset.getargs(x, 1, 1, 'pushdate requires one argument')

    ds = revset.getstring(l[0], 'pushdate requires a string argument')
    dm = util.matchdate(ds)

    def getrevs():
        for pushid, who, when, nodes in repo.pushlog.pushes():
            if dm(when):
                for node in nodes:
                    yield repo[node].rev()

    return subset & revset.generatorset(getrevs())

def revset_pushuser(repo, subset, x):
    """``pushuser(string)``

    User name that pushed the changeset contains string. The match is
    case-insensitive.

    If `string` starts with `re:`, the remainder of the string is treated as
    a regular expression. To match a user that actually contains `re:`, use
    the prefix `literal:`.
    """
    l = revset.getargs(x, 1, 1, 'pushuser requires one argument')
    n = encoding.lower(revset.getstring(l[0], 'pushuser requires a string'))
    kind, pattern, matcher = revset._substringmatcher(n)

    def getrevs():
        for pushid, who, when, nodes in repo.pushlog.pushes():
            if matcher(encoding.lower(who)):
                for node in nodes:
                    yield repo[node].rev()

    return subset & revset.generatorset(getrevs())

@command('verifypushlog', [], 'verify the pushlog data is sane')
def verifypushlog(ui, repo):
    """Verify the pushlog data looks correct."""
    return repo.pushlog.verify()

def extsetup(ui):
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)
    extensions.wrapfunction(exchange.pulloperation, 'closetransaction',
        exchangepullpushlog)

    revset.symbols['pushhead'] = revset_pushhead
    revset.symbols['pushdate'] = revset_pushdate
    revset.symbols['pushuser'] = revset_pushuser

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
