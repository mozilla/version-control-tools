# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''Record pushes to Mercurial repositories.'''

from __future__ import absolute_import

import collections
import contextlib
import os
import sqlite3
import stat
import time

from mercurial.node import bin, hex
from mercurial import (
    configitems,
    encoding,
    error,
    exchange,
    extensions,
    localrepo,
    pycompat,
    registrar,
    revset,
    templateutil,
    util,
    wireprotov1server as wireproto,
)
from mercurial.hgweb import (
    webutil,
)
from mercurial.utils import (
    dateutil,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())


Abort = error.Abort
RepoLookupError = error.RepoLookupError

minimumhgversion = b'4.8'
testedwith = b'4.8 4.9 5.0 5.1 5.2 5.3 5.4 5.5'
buglink = b'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20Pushlog'

cmdtable = {}
command = registrar.command(cmdtable)

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'pushlog', b'autolanduser',
           default=configitems.dynamicdefault)
configitem(b'pushlog', b'landingworkeruser',
           default=configitems.dynamicdefault)
configitem(b'pushlog', b'landingworkeruserdev',
           default=configitems.dynamicdefault)
configitem(b'pushlog', b'remoteuserprefix',
           default=None)
configitem(b'pushlog', b'timeoutro',
           default=configitems.dynamicdefault)
configitem(b'pushlog', b'timeoutrw',
           default=configitems.dynamicdefault)
configitem(b'pushlog', b'userprefix',
           default=None)


revsetpredicate = registrar.revsetpredicate()

SCHEMA = [
    'CREATE TABLE IF NOT EXISTS changesets (pushid INTEGER, rev INTEGER, node text)',
    'CREATE TABLE IF NOT EXISTS pushlog (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, date INTEGER)',
    'CREATE UNIQUE INDEX IF NOT EXISTS changeset_node ON changesets (node)',
    'CREATE UNIQUE INDEX IF NOT EXISTS changeset_rev ON changesets (rev)',
    'CREATE INDEX IF NOT EXISTS changeset_pushid ON changesets (pushid)',
    'CREATE INDEX IF NOT EXISTS pushlog_date ON pushlog (date)',
    'CREATE INDEX IF NOT EXISTS pushlog_user ON pushlog (user)',
]

AUTOLAND_USER = b'bind-autoland@mozilla.com'
LANDING_WORKER_USER = b'lando_landing_worker@mozilla.com'
LANDING_WORKER_USER_DEV = b'lando_landing_worker_dev@mozilla.com'


# Wraps capabilities wireproto command to advertise pushlog availability.
def capabilities(orig, repo, proto):
    caps = orig(repo, proto)
    caps.append(b'pushlog')
    return caps

@wireproto.wireprotocommand(b'pushlog', b'firstpush', permission=b'pull')
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
    lines = [b'1']

    try:
        firstpush = int(firstpush)

        for pushid, who, when, nodes in repo.pushlog.pushes(start_id=firstpush):
            lines.append(b'%d %s %d %s' % (pushid, who, when, b' '.join(nodes)))

        return b'\n'.join(lines)
    except Exception as e:
        return b'\n'.join([b'0', pycompat.bytestr(e)])


def exchangepullpushlog(orig, pullop):
    """This is called during pull to fetch pushlog data.

    The goal of this function is to replicate the entire pushlog. This is
    in contrast to replicating only the pushlog data for changesets the
    client has pulled. Put another way, this attempts complete replication
    as opposed to partial, hole-y replication.
    """
    # check stepsdone for future compatibility with bundle2 pushlog exchange.
    res = orig(pullop)

    if b'pushlog' in pullop.stepsdone or not pullop.remote.capable(b'pushlog'):
        return res

    pullop.stepsdone.add(b'pushlog')
    repo = pullop.repo
    urepo = repo.unfiltered()
    fetchfrom = repo.pushlog.lastpushid() + 1
    lines = pullop.remote._call(b'pushlog', firstpush=pycompat.bytestr(fetchfrom))
    lines = iter(lines.splitlines())

    statusline = pycompat.bytestr(next(lines))
    if statusline[0] == b'0':
        raise Abort(b'remote error fetching pushlog: %s' % next(lines))
    elif statusline != b'1':
        raise Abort(b'error fetching pushlog: unexpected response: %s\n' %
            statusline)

    pushes = []
    for line in lines:
        pushid, who, when, nodes = line.split(b' ', 3)
        nodes = [bin(n) for n in nodes.split()]

        # We stop processing if there is a reference to an unknown changeset.
        # This can happen in a few scenarios.
        #
        # Since the server streams *all* pushlog entries (from a starting
        # number), it could send pushlog entries for changesets the client
        # didn't request or were pushed since the client started pulling.
        #
        # If the remote repo contains obsolete changesets, we may see a
        # reference to a hidden changeset that was never transferred locally.
        #
        # The important thing we want to prevent is a reference to a locally
        # unknown changeset appearing in the pushlog.
        #
        # On hg.mo, there is a hack that transfers hidden changesets during
        # pulls. So when operating in mirror mode on that server, we should
        # never have locally unknown changesets.
        try:
            # Test against unfiltered repo so we can record entries for hidden
            # changesets.
            [urepo[n] for n in nodes]
        except error.RepoLookupError:
            missing = [hex(n) for n in nodes if n not in urepo]
            repo.ui.warn(b'received pushlog entry for unknown changeset %s; '
                         b'ignoring\n' % b', '.join(missing))
            break

        pushes.append((int(pushid), who, int(when), nodes))

    repo.pushlog.recordpushes(pushes, tr=pullop.trmanager.transaction())
    repo.ui.status(b'added %d pushes\n' % len(pushes))

    return res


def addpushmetadata(repo, ctx, d):
    if not util.safehasattr(repo, 'pushlog'):
        return

    push = repo.pushlog.pushfromchangeset(ctx)
    if push:
        d[b'pushid'] = push.pushid
        d[b'pushuser'] = push.user
        d[b'pushdate'] = dateutil.makedate(push.when)
        d[b'pushnodes'] = push.nodes
        d[b'pushhead'] = push.nodes[-1]


def commonentry(orig, repo, ctx):
    """Wraps webutil.commonentry to provide pushlog metadata to templates."""
    d = orig(repo, ctx)
    addpushmetadata(repo, ctx, d)
    return d


Push = collections.namedtuple('Push', ('pushid', 'user', 'when', 'nodes'))


def make_post_close(repo, conn):
    """Make a function to be called when a Mercurial transaction closes."""
    def pushlog_tr_post_close(tr):
        for attempt in range(3):
            try:
                conn.commit()
                conn.close()

                return
            except sqlite3.OperationalError as e:
                repo.ui.write(b'error committing pushlog transaction on'
                              b' attempt %d; retrying\n' % (attempt + 1))
                repo.ui.log(b'pushlog', b'Exception: %s' % pycompat.bytestr(e))
                time.sleep(attempt * 1.0)
        else:
            raise error.Abort(b'could not complete push due to pushlog operational errors; '
                              b'please retry, and file a bug if the issue persists')

    return pushlog_tr_post_close


def make_abort(repo, conn):
    """Make a function to be called when a Mercurial transaction aborts."""
    def pushlog_tr_abort(tr):
        if tr:
            # TRACKING hg48 - report is now private
            if util.safehasattr(tr, '_report'):
                tr._report(b'rolling back pushlog\n')
            else:
                tr.report(b'rolling back pushlog\n')

        conn.close()

    return pushlog_tr_abort


class pushlog(object):
    '''An interface to pushlog data.'''

    def __init__(self, repo):
        '''Create an instance bound to a sqlite database in a path.'''
        # Use a weak ref to avoid cycle. This object's lifetime should be no
        # greater than the repo's.
        self.repo = repo

        # Caches of pushlog data to avoid database I/O.
        # int -> Push
        self._push_by_id = {}
        # bin node -> int
        self._push_id_by_node = {}

    def _getconn(self, readonly=False, tr=None):
        """Get a SQLite connection to the pushlog.

        In normal operation, this will return a ``sqlite3.Connection``.
        If the database does not exist, it will be created. If the database
        schema is not present or up to date, it will be updated. An error will
        be raised if any of this could not be performed.

        If ``readonly`` is truthy, ``None`` will be returned if the database
        file does not exist. This gives read-only consumers the opportunity to
        short-circuit if no data is available.

        If ``tr`` is specified, it is a Mercurial transaction instance that
        this connection will be tied to. The connection will be committed and
        closed when the transaction is committed. The connection will roll back
        and be closed if the transaction is aborted.
        """
        path = self.repo.vfs.join(b'pushlog2.db')
        create = False
        if not os.path.exists(path):
            if readonly:
                return None

            create = True

        # A note on SQLite connection behavior.
        #
        # Most "modern" SQLite databases use the Write-Ahead Log (WAL). This
        # is a superior storage mechanism because it is faster and allows
        # concurrent readers and writers.
        #
        # Unfortunately, the WAL doesn't work well with network filesystems
        # like NFS because the WAL index relies on shared memory (which is
        # machine specific). It is possible to not use shared memory by setting
        # the locking_mode to EXCLUSIVE. However, this prevents concurrent
        # readers, which is obviously not desirable.
        #
        # Use of the WAL for the pushlog is not possible if network filesystem
        # or concurrent access are a requirement.
        #
        # Non-use of the WAL means that there will be reader and writer
        # contention. e.g. an active reader can block a writer.
        #
        # By default, SQLite defers obtaining a RESERVED (write) lock until
        # commit time. This can be moved to ``BEGIN TRANSACTION`` by using
        # IMMEDIATE. However, this will prevent new readers from connecting.
        # Since we want the database to be available to readers as much as
        # possible, deferring the lock until COMMIT time is desirable.
        #
        # If a Mercurial transaction is passed to this function, the SQLite
        # implicit/active transaction will be tied to that Mercurial
        # transaction. If Mercurial's transaction aborts, the SQLite transaction
        # is rolled back. If Mercurial's transaction closes, the SQLite
        # transaction is committed. If the database handle is closed without
        # an explicit Mercurial transaction close or abort, the default SQLite
        # behavior is to roll back the transaction.
        #
        # Note that the SQLite commit occurs *after* Mercurial's transaction
        # has been committed. There is the potential for Mercurial's transaction
        # to commit but SQLite's to fail. This is obviously not desirable.
        # However, without the ability to easily roll back the last committed
        # transaction in either Mercurial or SQLite, our hands are tied as
        # to how to achieve atomic changes. Our hacky solution is to increase
        # the busy timeout before commit to maximize the chances for a
        # successful SQLite commit.

        if readonly:
            option = b'timeoutro'
            default = 10000
        else:
            option = b'timeoutrw'
            default = 30000

        timeout = self.repo.ui.configint(b'pushlog', option, default)
        timeout = float(timeout) / 1000.0

        conn = sqlite3.connect(pycompat.sysstr(path), timeout=timeout,
                               detect_types=sqlite3.PARSE_DECLTYPES)
        conn.text_factory = pycompat.bytestr

        if not create:
            res = conn.execute(
                "SELECT COUNT(*) FROM SQLITE_MASTER WHERE name='pushlog'")
            if res.fetchone()[0] != 1:
                create = True

        if tr:
            tr.addpostclose(b'pushlog', make_post_close(self.repo, conn))
            tr.addabort(b'pushlog', make_abort(self.repo, conn))

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
        c = self._getconn(tr=self.repo._transref())

        # Operate against unfiltered repo so we can insert entries for hidden
        # changesets.
        repo = self.repo.unfiltered()

        # Now that the hooks are installed, any exceptions will result in db
        # close via one of our abort handlers.
        res = c.execute('INSERT INTO pushlog (user, date) VALUES (?, ?)',
                        (pycompat.sysstr(user), when))
        pushid = res.lastrowid
        for e in nodes:
            ctx = repo[e]
            rev = ctx.rev()
            node = ctx.hex()

            c.execute('INSERT INTO changesets (pushid, rev, node) '
                      'VALUES (?, ?, ?)', (pushid, rev, pycompat.sysstr(node)))

    def recordpushes(self, pushes, tr):
        """Record multiple pushes.

        This is effectively a version of ``recordpush()`` that accepts multiple
        pushes.

        It accepts in iterable of tuples:

          (pushid, user, time, nodes)

        Where ``nodes`` is an iterable of changeset identifiers (both bin and
        hex forms are accepted).

        The ``tr`` argument defines a Mercurial transaction to tie this
        operation to.
        """
        c = self._getconn(tr=tr)

        # Operate against unfiltered repo so we can insert entries for hidden
        # changesets.
        repo = self.repo.unfiltered()

        for pushid, user, when, nodes in pushes:
            c.execute('INSERT INTO pushlog (id, user, date) VALUES (?, ?, ?)',
                (pushid, pycompat.sysstr(user), when))
            for n in nodes:
                ctx = repo[n]
                rev = ctx.rev()
                node = ctx.hex()

                c.execute('INSERT INTO changesets (pushid, rev, node) '
                          'VALUES (?, ?, ?)', (pushid, rev, pycompat.sysstr(node)))

    def lastpushid(self, conn=None):
        """Obtain the integer pushid of the last known push."""
        def query(c):
            res = c.execute('SELECT id from pushlog ORDER BY id DESC').fetchone()
            if not res:
                return 0
            return res[0]

        if conn:
            return query(conn)
        else:
            with self.conn(readonly=True) as c:
                if not c:
                    return 0

                return query(c)

    def last_push_id_replicated(self, conn=None):
        """Obtain the integer push id of the last replicated push."""
        actual = self.lastpushid(conn=conn)

        # If replicated data isn't available or the last push id isn't recorded,
        # there's nothing special to do.
        data = getattr(self.repo, r'replicated_data', None)

        if data and data[b'last_push_id'] is not None:
            return min(data[b'last_push_id'], actual)

        return actual

    def pushes(self, start_id=None, start_id_exclusive=False,
               end_id=None, end_id_exclusive=False,
               reverse=False, limit=None, offset=None,
               users=None,
               start_time=None, start_time_exclusive=False,
               end_time=None, end_time_exclusive=False,
               start_node=None, start_node_exclusive=False,
               end_node=None, end_node_exclusive=False,
               nodes=None,
               only_replicated=False):
        """Return information about pushes to this repository.

        This is a generator of Push namedtuples describing each push. Each
        tuple has the form:

            (pushid, who, when, [nodes])

        Nodes are returned in their 40 byte hex form.

        ``start_id`` and ``end_id`` define the lower and upper bounds for
        numeric push IDs. ``start_id_exclusive`` and ``end_end_exclusive`` can
        be used to make the boundary condition exclusive instead of inclusive.

        ``start_time`` and ``end_time`` define a lower and upper limit for the
        push time, as specified in seconds since UNIX epoch.
        ``start_time_exclusive`` and ``end_time_exclusive`` can be used to make
        the boundary condition exclusive instead of inclusive.

        ``start_node`` and ``end_node`` define a lower and upper limit for
        pushes as defined by a push containing a revision.
        ``start_node_exclusive`` and ``end_node_exclusive`` can be used to make
        the boundary condition exclusive instead of inclusive.

        ``nodes`` is an iterable of revision identifiers. If specified, only
        pushes containing nodes from this set will be returned.

        ``users`` is an iterable of push users to limit results to.

        ``reverse`` can be used to return pushes from most recent to oldest
        instead of the default of oldest to newest.

        ``offset`` can be used to skip the first N pushes that would be
        returned.

        ``limit`` can be used to limit the number of returned pushes to that
        count.

        ``only_replicated`` can be specified to only include info about pushes
        that have been fully replicated.

        When multiple filters are defined, they are logically ANDed together.
        """
        if start_id is not None and start_node is not None:
            raise ValueError('cannot specify both start_id and start_node')

        if end_id is not None and end_node is not None:
            raise ValueError('cannot specify both end_id and end_node')

        with self.conn(readonly=True) as c:
            if not c:
                return

            start_id = start_id if start_id is not None else 0

            # We further refine start_id and end_id by nodes, if specified.
            # We /could/ do this in a single SQL statement. But that would
            # make the level of nesting a bit complicated. So we just issue
            # an extra SQL statement to resolve the push id from a node.
            if start_node is not None:
                start_node = self.repo.lookup(start_node)
                start_push = self.pushfromnode(start_node)
                # If the changeset exists, but wasn't pushed,
                # start at 0.
                start_id = start_push.pushid if start_push else 0
                start_id_exclusive = start_node_exclusive

            if end_node is not None:
                end_node = self.repo.lookup(end_node)
                end_id = self.pushfromnode(end_node).pushid
                end_id_exclusive = end_node_exclusive

            op = '>' if start_id_exclusive else '>='

            # In order to support LIMIT and OFFSET at the push level,
            # we need to use an inner SELECT to apply the filtering there.
            # That's because LIMIT and OFFSET apply to the SELECT as a whole.
            # Since we're doing a LEFT JOIN, LIMIT and OFFSET would count nodes,
            # not pushes.
            inner_q = ('SELECT id, user, date FROM pushlog '
                       'WHERE id %s ? ' % op)
            args = [start_id]

            if end_id is not None:
                op = '<' if end_id_exclusive else '<='
                inner_q += 'AND id %s ? ' % op
                args.append(end_id)

            if start_time is not None:
                op = '>' if start_time_exclusive else '>='
                inner_q += 'AND date %s ? ' % op
                args.append(start_time)

            if end_time is not None:
                op = '<' if end_time_exclusive else '<='
                inner_q += 'AND date %s ? ' % op
                args.append(end_time)

            user_q = []
            for user in users or []:
                user_q.append('user=?')
                # `user` will be a byte string, but later on
                # we attempt to use it as a value for a unicode
                # format string. The operation succeeds but our
                # query returns no results as the value is improperly
                # represented in unicode. So decode here before
                # passing to sqlite
                args.append(pycompat.sysstr(user))

            if user_q:
                inner_q += 'AND (%s) ' % ' OR '.join(user_q)

            # We include the push for each listed node. We do this via multiple
            # subqueries to select the pushid for each node.
            node_q = []
            for node in nodes or []:
                node_q.append('id=(SELECT pushid FROM changesets WHERE node=?)')
                args.append(
                    pycompat.sysstr(hex(self.repo.lookup(node)))
                )

            if node_q:
                inner_q += 'AND (%s) ' % ' OR '.join(node_q)

            # Implement max push ID filtering separately from end_id. This makes
            # things simpler, as we don't need to take inclusive/exclusive into
            # play.
            if only_replicated:
                max_push_id = self.last_push_id_replicated(conn=c)
            else:
                max_push_id = self.lastpushid(conn=c)

            inner_q += 'AND id <= ? '
            args.append(max_push_id)

            if reverse:
                inner_q += 'ORDER BY id DESC '
            else:
                inner_q += 'ORDER BY id ASC '

            if limit is not None:
                inner_q += 'LIMIT ? '
                args.append(limit)

            if offset is not None:
                inner_q += 'OFFSET ? '
                args.append(offset)

            q = ('SELECT id, user, date, rev, node FROM (%s) '
                 'LEFT JOIN changesets on id=pushid ' % inner_q)

            if reverse:
                q += 'ORDER BY id DESC, rev DESC '
            else:
                q += 'ORDER BY id ASC, rev ASC '

            res = c.execute(q, args)

            lastid = None
            current = None
            for pushid, who, when, rev, node in res:
                if pushid != lastid:
                    if current:
                        yield current
                    lastid = pushid
                    current = Push(pushid, who, when, [])
                    if node:
                        current.nodes.append(node)
                else:
                    current.nodes.append(node)

            if current:
                yield current

    def push_count(self):
        """Obtain the number of pushes in the database."""
        with self.conn(readonly=True) as c:
            if not c:
                return 0

            return c.execute('SELECT COUNT(*) FROM pushlog').fetchone()[0]

    def pushfromnode(self, node):
        """Obtain info about a push that added the specified changeset.

        Returns a Push namedtuple of (pushid, who, when, [nodes]) or None if
        there is no pushlog info for this node.

        Argument is specified as binary node.
        """
        if node in self._push_id_by_node:
            pushid = self._push_id_by_node[node]
            return self._push_by_id[pushid] if pushid is not None else None

        with self.conn(readonly=True) as c:
            if not c:
                return None

            return self._push_from_node(c, node)

    def _push_from_node(self, conn, node):
        res = conn.execute('SELECT pushid from changesets WHERE node=?',
                           (pycompat.sysstr(hex(node)),)).fetchone()
        if not res:
            return None

        return self.pushfromid(conn, res[0])

    def pushfromchangeset(self, ctx):
        return self.pushfromnode(ctx.node())

    def pushfromid(self, conn, pushid):
        """Obtain a push from its numeric push id.

        Returns a Push namedtuple or None if there is no push with this push
        id.
        """
        push = self._push_by_id.get(pushid)
        if push:
            return push

        res = conn.execute('SELECT id, user, date, node from pushlog '
                           'LEFT JOIN changesets on id=pushid '
                           'WHERE id=? ORDER BY rev ASC', (pushid,))
        nodes = []
        for pushid, who, when, node in res:
            nodes.append(node)

        if not nodes:
            return None

        return Push(pushid, who, when, nodes)

    @contextlib.contextmanager
    def cache_data_for_nodes(self, nodes):
        """Given an iterable of nodes, cache pushlog data for them.

        Due to current API design, many pushlog methods open a SQLite
        database, perform a query, then close the database. Calling these
        within tight loops can be slow.

        This context manager can be used to pre-load pushlog data to
        avoid inefficient SQLite access patterns.
        """
        with self.conn(readonly=True) as c:
            if not c:
                return

            try:
                for node in nodes:
                    push = self._push_from_node(c, node)
                    if push:
                        self._push_id_by_node[node] = push.pushid
                        self._push_by_id[push.pushid] = push
                    else:
                        self._push_id_by_node[node] = None

                yield
            finally:
                self._push_id_by_node = {}
                self._push_by_id = {}

    def verify(self):
        # Attempt to create database (since .pushes below won't).
        with self.conn():
            pass

        repo = self.repo
        ui = self.repo.ui

        ret = 0
        seennodes = set()
        pushcount = 0
        for pushcount, push in enumerate(self.pushes(), 1):
            if not push.nodes:
                ui.warn(b'pushlog entry has no nodes: #%s\n' %
                        pycompat.bytestr(push.pushid))
                continue

            for node in push.nodes:
                try:
                    repo[node]
                except RepoLookupError:
                    ui.warn(b'changeset in pushlog entry #%s does not exist: %s\n' %
                            (pycompat.bytestr(push.pushid), pycompat.bytestr(node)))
                    ret = 1

                seennodes.add(bin(node))

        for rev in repo:
            ctx = repo[rev]
            if ctx.node() not in seennodes:
                ui.warn(b'changeset does not exist in pushlog: %s\n' % ctx.hex())
                ret = 1

        if ret:
            ui.status(b'pushlog has errors\n')
        else:
            ui.status(b'pushlog contains all %d changesets across %d pushes\n' %
                (len(seennodes), pushcount))

        return ret

    def handledestroyed(self):
        """Handle a destroyed event in the repository.

        This is called when changesets have been destroyed from the repository.
        This function will reconcile the state of the pushlog to match new
        reality.

        Push IDs are explicitly not deleted. However, they may become empty.
        """
        repo = self.repo

        with self.conn() as c:
            if not c:
                return

            res = c.execute('SELECT pushid, rev, node FROM changesets '
                            'ORDER BY pushid, rev ASC')

            deletes = []
            revupdates = []

            for pushid, rev, node in res:
                try:
                    ctx = repo[node]
                    # Changeset has new ordering in revlog. Correct it.
                    if ctx.rev() != rev:
                        revupdates.append((node, ctx.rev()))
                        repo.ui.warn(b'changeset rev will be updated in '
                                     b'pushlog: %s\n' % node)
                except RepoLookupError:
                    # The changeset was stripped. Remove it from the pushlog.
                    deletes.append(node)
                    repo.ui.warn(b'changeset will be deleted from '
                                 b'pushlog: %s\n' % node)

            for node in deletes:
                c.execute('DELETE FROM changesets WHERE node = ?', (pycompat.sysstr(node),))

            if deletes:
                repo.ui.log(b'pushlog',
                            b'deleted %d changesets from pushlog: %s\n' % (
                            len(deletes), b', '.join(deletes)))

            for node, rev in revupdates:
                c.execute('UPDATE changesets SET rev=? WHERE node=?',
                          (rev, pycompat.sysstr(node)))

            if revupdates:
                repo.ui.log(b'pushlog',
                            b'reordered %d changesets in pushlog\n' %
                            len(revupdates))

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
    if source not in (b'push', b'serve'):
        ui.note(b'(not updating pushlog since changesets come from %s)\n' % source)
        return 0

    # REMOTE_USER comes from authenticated Apache httpd request.
    # USER comes from SSH.
    # Both are implicitly trusted.
    # Since the usernames could come from separate auth databases, we support
    # prefixing the user with an identifier to distinguish which source the
    # user came from.

    # WSGI environment variables are passed in as part of the request data.
    # hgweb sets the WSGI environment variables on ui.environ but not in
    # os.environ. For SSH, ui.environ should be equivalent to os.environ.
    remoteuser = ui.environ.get(b'REMOTE_USER',
                                encoding.environ.get(b'REMOTE_USER'))
    user = encoding.environ.get(b'USER')
    if not remoteuser and not user:
        ui.write(b'authenticated user not found; '
                 b'refusing to write into pushlog\n')
        return 1

    # If the push user is in landing_users, we check the AUTOLAND_REQUEST_USER
    # environment variable. If set, we use that as the user in the pushlog
    # rather than the pusher. This allows us to track who actually
    # initiated the push.
    landing_users = (
        ui.config(b'pushlog', b'autolanduser', AUTOLAND_USER),
        ui.config(b'pushlog', b'landingworkeruser', LANDING_WORKER_USER),
        ui.config(b'pushlog', b'landingworkeruserdev', LANDING_WORKER_USER_DEV),
    )

    if user in landing_users:
        ui.write(b'autoland or landing worker push detected\n')
        user = os.environ.get('AUTOLAND_REQUEST_USER', user)

    remoteprefix = ui.config(b'pushlog', b'remoteuserprefix')
    userprefix = ui.config(b'pushlog', b'userprefix')

    if remoteprefix and remoteuser:
        remoteuser = b'%s:%s' % (remoteprefix, remoteuser)

    if userprefix and user:
        user = b'%s:%s' % (userprefix, user)

    pushuser = remoteuser or user

    try:
        t = int(time.time())
        revs = range(repo[node].rev(), len(repo))
        repo.pushlog.recordpush(revs, pushuser, t)
        ui.write(b'recorded push in pushlog\n')
        return 0
    except Exception as e:
        ui.write(b'error recording into pushlog (%s); please retry your '
                 b'push\n' % pycompat.bytestr(e.args[0]))

    return 1


@revsetpredicate(b'pushhead()', safe=True)
def revset_pushhead(repo, subset, x):
    """``pushhead()``

    Changesets that were heads when they were pushed.
    """
    revset.getargs(x, 0, 0, b'pushhead takes no arguments')

    # Iterating over all pushlog data is unfortunate, as there is overhead
    # involved. However, this is less overhead than issuing a SQL query for
    # every changeset, especially on large repositories. There is room to make
    # this optimal by batching SQL, but that adds complexity. For now,
    # simplicity wins.
    def getrevs():
        to_rev = repo.changelog.rev
        for push in repo.pushlog.pushes():
            yield to_rev(bin(push.nodes[-1]))

    return subset & revset.generatorset(getrevs())


@revsetpredicate(b'pushdate(interval)', safe=True)
def revset_pushdate(repo, subset, x):
    """``pushdate(interval)``

    Changesets that were pushed within the interval. See :hg:`help dates`.
    """
    l = revset.getargs(x, 1, 1, b'pushdate requires one argument')

    ds = revset.getstring(l[0], b'pushdate requires a string argument')
    dm = dateutil.matchdate(ds)

    def getrevs():
        to_rev = repo.changelog.rev
        for push in repo.pushlog.pushes():
            if dm(push.when):
                for node in push.nodes:
                    yield to_rev(bin(node))

    return subset & revset.generatorset(getrevs())


@revsetpredicate(b'pushuser(string)', safe=True)
def revset_pushuser(repo, subset, x):
    """``pushuser(string)``

    User name that pushed the changeset contains string.

    The match is case-insensitive.

    If `string` starts with `re:`, the remainder of the string is treated as
    a regular expression. To match a user that actually contains `re:`, use
    the prefix `literal:`.
    """
    l = revset.getargs(x, 1, 1, b'pushuser requires one argument')
    n = encoding.lower(revset.getstring(l[0], b'pushuser requires a string'))
    kind, pattern, matcher = revset._substringmatcher(n)

    def getrevs():
        to_rev = repo.changelog.rev
        for push in repo.pushlog.pushes():
            if matcher(encoding.lower(push.user)):
                for node in push.nodes:
                    yield to_rev(bin(node))

    return subset & revset.generatorset(getrevs())


@revsetpredicate(b'pushid(int)', safe=True)
def revset_pushid(repo, subset, x):
    """``pushid(int)``

    Changesets that were part of the specified numeric push id.
    """
    l = revset.getargs(x, 1, 1, b'pushid requires one argument')
    try:
        pushid = int(revset.getstring(l[0], b'pushid requires a number'))
    except (TypeError, ValueError):
        raise error.ParseError(b'pushid expects a number')

    with repo.pushlog.conn(readonly=True) as conn:
        push = repo.pushlog.pushfromid(conn, pushid) if conn else None

    if not push:
        return revset.baseset()

    to_rev = repo.changelog.rev
    pushrevs = set()
    for node in push.nodes:
        try:
            pushrevs.add(to_rev(bin(node)))
        except RepoLookupError:
            pass

    return subset & pushrevs


@revsetpredicate(b'pushrev(set)', safe=True)
def revset_pushrev(repo, subset, x):
    """``pushrev(set)``

    Changesets that were part of the same push as the specified changeset(s).
    """
    l = revset.getset(repo, subset, x)

    # This isn't the most optimal implementation, especially if the input
    # set is large. But it gets the job done.
    to_rev = repo.changelog.rev
    revs = set()
    for rev in l:
        push = repo.pushlog.pushfromchangeset(repo[rev])
        if push:
            for node in push.nodes:
                revs.add(to_rev(bin(node)))

    return subset.filter(revs.__contains__)

# Again, for performance reasons we read the entire pushlog database and cache
# the results. Again, this is unfortunate. But, the alternative is a potential
# very expensive series of database lookups.
#
# The justification for doing this for templates is even less than doing it for
# revsets because where revsets typically need to operate on lots of
# changesets, templates typically only render a small handful of changesets.
# Performing a query for each changeset being templatized is an easier pill to
# swallow. Depending on how these templates are used in the wild, we should
# revisit the decision to precache the pushlog.

def _getpushinfo(repo, ctx, cache):
    if b'nodetopush' not in cache:
        nodetopush = {}
        for push in repo.pushlog.pushes():
            for node in push.nodes:
                nodetopush[node] = push

        cache[b'nodetopush'] = nodetopush

    return cache[b'nodetopush'].get(ctx.hex(), (None, None, None, None))


keywords = {}
templatekeyword = registrar.templatekeyword(keywords)


@templatekeyword(b'pushid', requires={b'repo', b'ctx', b'cache'})
def template_pushid(context, mapping):
    """:pushid: Integer. The unique identifier for the push that introduced
    this changeset.
    """
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    cache = context.resource(mapping, b'cache')

    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return pushid


@templatekeyword(b'pushuser', requires={b'repo', b'ctx', b'cache'})
def template_pushuser(context, mapping):
    """:pushuser: String. The user who pushed this changeset."""
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    cache = context.resource(mapping, b'cache')

    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return who


@templatekeyword(b'pushdate', requires={b'repo', b'ctx', b'cache'})
def template_pushdate(context, mapping):
    """:pushdate: Date information. When this changeset was pushed."""
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    cache = context.resource(mapping, b'cache')

    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return templateutil.date(dateutil.makedate(when), showfmt=b'%d.0%d') \
        if when else None


@templatekeyword(b'pushbasenode', requires={b'repo', b'ctx', b'cache'})
def template_pushbasenode(context, mapping):
    """:pushbasenode: String. The changeset identification hash, as a 40 digit
    hexadecimal string, that was the first/base node for the push this
    changeset was part of.
    """
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    cache = context.resource(mapping, b'cache')

    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return nodes[0] if nodes else None


@templatekeyword(b'pushheadnode', requires={b'repo', b'ctx', b'mapping'})
def template_pushheadnode(context, mapping):
    """:pushheadnode: String. The changeset identification hash, as a 40 digit
    hexadecimal string, that was the head for the push this changeset was
    part of.
    """
    repo = context.resource(mapping, b'repo')
    ctx = context.resource(mapping, b'ctx')
    cache = context.resource(mapping, b'cache')

    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return nodes[-1] if nodes else None

@command(b'verifypushlog', [], b'verify the pushlog data is sane')
def verifypushlog(ui, repo):
    """Verify the pushlog data looks correct."""
    return repo.pushlog.verify()

def extsetup(ui):
    extensions.wrapfunction(wireproto, b'_capabilities', capabilities)
    extensions.wrapfunction(exchange, b'_pullobsolete', exchangepullpushlog)

    extensions.wrapfunction(webutil, b'commonentry', commonentry)


def reposetup(ui, repo):
    if not repo.local():
        return

    ui.setconfig(b'hooks', b'pretxnchangegroup.pushlog', pretxnchangegrouphook, b'pushlog')

    class pushlogrepo(repo.__class__):
        # We /may/ be able to turn this into a property cache without the
        # filesystem check. But the filesystem check is safer in case pushlog
        # mutation invalidates cached state on type instances.
        @localrepo.repofilecache(b'pushlog2.db')
        def pushlog(self):
            return pushlog(self)

        def destroyed(self):
            super(pushlogrepo, self).destroyed()
            self.pushlog.handledestroyed()

    repo.__class__ = pushlogrepo
