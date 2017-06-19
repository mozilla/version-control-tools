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
    cmdutil,
    encoding,
    error,
    exchange,
    extensions,
    localrepo,
    registrar,
    revset,
    templatekw,
    util,
    wireproto,
)
from mercurial.hgweb import (
    webutil,
)

Abort = error.Abort
RepoLookupError = error.RepoLookupError

minimumhgversion = '4.1'
testedwith = '4.1 4.2'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20Pushlog'

cmdtable = {}
command = cmdutil.command(cmdtable)

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

AUTOLAND_USER = 'bind-autoland@mozilla.com'


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
    """This is called during pull to fetch pushlog data.

    The goal of this function is to replicate the entire pushlog. This is
    in contrast to replicating only the pushlog data for changesets the
    client has pulled. Put another way, this attempts complete replication
    as opposed to partial, hole-y replication.
    """
    # check stepsdone for future compatibility with bundle2 pushlog exchange.
    res = orig(pullop)

    if 'pushlog' in pullop.stepsdone or not pullop.remote.capable('pushlog'):
        return res

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

        # We stop processing if there is a reference to an unknown changeset.
        # This can happen in a few scenarios.
        #
        # Since the server streams *all* pushlog entries (from a starting
        # number), it could send pushlog entries for changesets the client
        # didn't request or were pushed since the client started pulling.
        #
        # If the remote repo contains obsolete changesets, we may see a
        # reference to a hidden changeset.
        #
        # This is arguably not the desirable behavior: pushlog replication
        # should be robust. However, doing things this way helps defend
        # against pushlog "corruption" since inserting references to unknown
        # changesets into the database is dangerous.
        try:
            [repo[n] for n in nodes]
        except error.RepoLookupError:
            repo.ui.warn('received pushlog entry for unknown changeset; ignoring\n')
            break

        pushes.append((int(pushid), who, int(when), nodes))

    repo.pushlog.recordpushes(pushes, tr=pullop.trmanager.transaction())
    repo.ui.status('added %d pushes\n' % len(pushes))

    return res


def addpushmetadata(repo, ctx, d):
    if not hasattr(repo, 'pushlog'):
        return

    push = repo.pushlog.pushfromchangeset(ctx)
    if push:
        d['pushid'] = push.pushid
        d['pushuser'] = push.user
        d['pushdate'] = util.makedate(push.when)
        d['pushnodes'] = push.nodes
        d['pushhead'] = push.nodes[-1]


def commonentry(orig, repo, ctx):
    """Wraps webutil.commonentry to provide pushlog metadata to templates."""
    d = orig(repo, ctx)
    addpushmetadata(repo, ctx, d)
    return d


Push = collections.namedtuple('Push', ('pushid', 'user', 'when', 'nodes'))


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

        # WARNING low-level hacks applied.
        #
        # The active transaction object provides various instance-specific
        # internal callbacks. When we run, the transaction object comes from
        # localrepository.transaction().
        #
        # The code here essentially ties transaction close/commit to DB
        # commit + close and transaction abort/rollback to DB close.
        # If the database is closed without a commit, the active database
        # transaction (our changes) will be rolled back.

        def onpostclose(tr):
            conn.commit()
            conn.close()

        def onabort(tr):
            if tr:
                tr.report('rolling back pushlog\n')
            conn.close()

        if tr:
            tr.addpostclose('pushlog', onpostclose)
            tr.addabort('pushlog', onabort)

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

        c = self._getconn(tr=self.repo._transref())

        # Now that the hooks are installed, any exceptions will result in db
        # close via one of our abort handlers.
        res = c.execute('INSERT INTO pushlog (user, date) VALUES (?, ?)', (user, when))
        pushid = res.lastrowid
        for e in nodes:
            ctx = self.repo[e]
            rev = ctx.rev()
            node = ctx.hex()

            c.execute('INSERT INTO changesets (pushid, rev, node) '
                    'VALUES (?, ?, ?)', (pushid, rev, node))

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

    def lastpushid(self):
        """Obtain the integer pushid of the last known push."""
        with self.conn() as c:
            res = c.execute('SELECT id from pushlog ORDER BY id DESC').fetchone()
            if not res:
                return 0
            return res[0]

    def pushes(self, startid=1):
        """Return information about pushes to this repository.

        This is a generator of Push namedtuples describing each push. Each
        tuple has the form:

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
                    current = Push(pushid, who, when, [])
                    if node:
                        current.nodes.append(node)
                else:
                    current.nodes.append(node)

            if current:
                yield current

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
                           (hex(node),)).fetchone()
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
            who = who.encode('utf-8')
            nodes.append(node.encode('ascii'))

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
                ui.warn('pushlog entry has no nodes: #%s\n' % push.pushid)
                continue

            for node in push.nodes:
                try:
                    repo[node]
                except RepoLookupError:
                    ui.warn('changeset in pushlog entry #%s does not exist: %s\n' %
                            (push.pushid, node))
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
                        repo.ui.warn('changeset rev will be updated in '
                                     'pushlog: %s\n' % node)
                except RepoLookupError:
                    # The changeset was stripped. Remove it from the pushlog.
                    deletes.append(node)
                    repo.ui.warn('changeset will be deleted from '
                                 'pushlog: %s\n' % node)

            for node in deletes:
                c.execute('DELETE FROM changesets WHERE node = ?', (node,))

            if deletes:
                repo.ui.log('pushlog',
                            'deleted %d changesets from pushlog: %s\n' % (
                            len(deletes), ', '.join(deletes)))

            for node, rev in revupdates:
                c.execute('UPDATE changesets SET rev=? WHERE node=?',
                          (rev, node))

            if revupdates:
                repo.ui.log('pushlog',
                            'reordered %d changesets in pushlog\n' %
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
    if source not in ('push', 'serve'):
        ui.note('(not updating pushlog since changesets come from %s)\n' % source)
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
    remoteuser = ui.environ.get('REMOTE_USER', os.environ.get('REMOTE_USER'))
    user = os.environ.get('USER')
    if not remoteuser and not user:
        ui.write('authenticated user not found; '
                 'refusing to write into pushlog\n')
        return 1

    # If the push user is the AUTOLAND_USER we check the AUTOLAND_REQUEST_USER
    # environment variable. If set, we use that as the user in the pushlog
    # rather than the pusher. This allows us to track who actually
    # initiated the push.
    autoland_user = ui.config('pushlog', 'autolanduser', AUTOLAND_USER)
    if user == autoland_user:
        ui.write('autoland push detected\n')
        user = os.environ.get('AUTOLAND_REQUEST_USER', user)

    remoteprefix = ui.config('pushlog', 'remoteuserprefix')
    userprefix = ui.config('pushlog', 'userprefix')

    if remoteprefix and remoteuser:
        remoteuser = '%s:%s' % (remoteprefix, remoteuser)

    if userprefix and user:
        user = '%s:%s' % (userprefix, user)

    pushuser = remoteuser or user

    try:
        t = int(time.time())
        revs = range(repo[node].rev(), len(repo))
        repo.pushlog.recordpush(revs, pushuser, t)
        ui.write('recorded push in pushlog\n')
        return 0
    except Exception:
        ui.write('error recording into pushlog; please retry your push\n')

    return 1


@revsetpredicate('pushhead()', safe=True)
def revset_pushhead(repo, subset, x):
    """Changesets that were heads when they were pushed.

    A push head is a changeset that was a head at the time it was pushed.
    """
    revset.getargs(x, 0, 0, 'pushhead takes no arguments')

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


@revsetpredicate('pushdate(interval)', safe=True)
def revset_pushdate(repo, subset, x):
    """Changesets that were pushed within the interval, see :hg:`help dates`."""
    l = revset.getargs(x, 1, 1, 'pushdate requires one argument')

    ds = revset.getstring(l[0], 'pushdate requires a string argument')
    dm = util.matchdate(ds)

    def getrevs():
        to_rev = repo.changelog.rev
        for push in repo.pushlog.pushes():
            if dm(push.when):
                for node in push.nodes:
                    yield to_rev(bin(node))

    return subset & revset.generatorset(getrevs())


@revsetpredicate('pushuser(string)', safe=True)
def revset_pushuser(repo, subset, x):
    """User name that pushed the changeset contains string.

    The match is case-insensitive.

    If `string` starts with `re:`, the remainder of the string is treated as
    a regular expression. To match a user that actually contains `re:`, use
    the prefix `literal:`.
    """
    l = revset.getargs(x, 1, 1, 'pushuser requires one argument')
    n = encoding.lower(revset.getstring(l[0], 'pushuser requires a string'))
    kind, pattern, matcher = revset._substringmatcher(n)

    def getrevs():
        to_rev = repo.changelog.rev
        for push in repo.pushlog.pushes():
            if matcher(encoding.lower(push.user)):
                for node in push.nodes:
                    yield to_rev(bin(node))

    return subset & revset.generatorset(getrevs())


@revsetpredicate('pushid(int)', safe=True)
def revset_pushid(repo, subset, x):
    """Changesets that were part of the specified numeric push id."""
    l = revset.getargs(x, 1, 1, 'pushid requires one argument')
    try:
        pushid = int(revset.getstring(l[0], 'pushid requires a number'))
    except (TypeError, ValueError):
        raise error.ParseError('pushid expects a number')

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


@revsetpredicate('pushrev(set)', safe=True)
def revset_pushrev(repo, subset, x):
    """Changesets that were part of the same push as the specified changeset(s)."""
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
    if 'nodetopush' not in cache:
        nodetopush = {}
        for push in repo.pushlog.pushes():
            for node in push.nodes:
                nodetopush[node] = push

        cache['nodetopush'] = nodetopush

    return cache['nodetopush'].get(ctx.hex(), (None, None, None, None))

def template_pushid(repo, ctx, templ, cache, **args):
    """:pushid: Integer. The unique identifier for the push that introduced
    this changeset.
    """
    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return pushid

def template_pushuser(repo, ctx, templ, cache, **args):
    """:pushuser: String. The user who pushed this changeset."""
    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return who

def template_pushdate(repo, ctx, templ, cache, **args):
    """:pushdate: Date information. When this changeset was pushed."""
    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return util.makedate(when) if when else None

def template_pushbasenode(repo, ctx, templ, cache, **args):
    """:pushbasenode: String. The changeset identification hash, as a 40 digit
    hexadecimal string, that was the first/base node for the push this
    changeset was part of.
    """
    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return nodes[0] if nodes else None

def template_pushheadnode(repo, ctx, templ, cache, **args):
    """:pushheadnode: String. The changeset identification hash, as a 40 digit
    hexadecimal string, that was the head for the push this changeset was
    part of.
    """
    pushid, who, when, nodes = _getpushinfo(repo, ctx, cache)
    return nodes[-1] if nodes else None

@command('verifypushlog', [], 'verify the pushlog data is sane')
def verifypushlog(ui, repo):
    """Verify the pushlog data looks correct."""
    return repo.pushlog.verify()

def extsetup(ui):
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)
    extensions.wrapfunction(exchange, '_pullobsolete', exchangepullpushlog)

    keywords = {
        'pushid': template_pushid,
        'pushuser': template_pushuser,
        'pushdate': template_pushdate,
        'pushbasenode': template_pushbasenode,
        'pushheadnode': template_pushheadnode,
    }

    templatekw.keywords.update(keywords)

    extensions.wrapfunction(webutil, 'commonentry', commonentry)


def reposetup(ui, repo):
    if not repo.local():
        return

    ui.setconfig('hooks', 'pretxnchangegroup.pushlog', pretxnchangegrouphook, 'pushlog')

    class pushlogrepo(repo.__class__):
        # We /may/ be able to turn this into a property cache without the
        # filesystem check. But the filesystem check is safer in case pushlog
        # mutation invalidates cached state on type instances.
        @localrepo.repofilecache('pushlog2.db')
        def pushlog(self):
            return pushlog(self)

        def destroyed(self):
            super(pushlogrepo, self).destroyed()
            self.pushlog.handledestroyed()

    repo.__class__ = pushlogrepo
