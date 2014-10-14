# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board client extension.

This extensions enables clients to easily create Review Board reviews
when pushing to a remote server.

When a client with this extension installed pushes to a remote that has the
corresponding server extension installed, the client will create a Review
Board review automatically.

This extension adds new options to the `push` command:

  * --noreview If present, we will not attempt to perform a review
    automatically when pushing. This is typically only useful for
    testing or ensuring certain commits are present on the remote.
  * --reviewid The review identifier to use. Pushes using the same
    review ID will overwrite existing reviews for that ID.
"""

import errno
import os
import sys
import urllib

from mercurial import cmdutil
from mercurial import commands
from mercurial import demandimport
from mercurial import exchange
from mercurial import extensions
from mercurial import hg
from mercurial import localrepo
from mercurial import obsolete
from mercurial import phases
from mercurial import scmutil
from mercurial import sshpeer
from mercurial import templatekw
from mercurial import util
from mercurial import wireproto
from mercurial.i18n import _
from mercurial.node import bin, hex

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

demandimport.disable()
try:
    import hgrb.proto
except ImportError:
    sys.path.insert(0, OUR_DIR)

    import hgrb.proto
demandimport.enable()

from mozautomation.commitparser import parse_bugs
from mozhg.auth import getbugzillaauth

testedwith = '3.0 3.0.1 3.0.2'

cmdtable = {}
command = cmdutil.command(cmdtable)

class ReviewID(object):
    """Represents a parsed review identifier."""

    def __init__(self, rid):
        self.bug = None
        self.user = None

        if not rid:
            return

        # Assume digits are Bugzilla bugs.
        if rid.isdigit():
            rid = 'bz://%s' % rid

        if rid and not rid.startswith('bz://'):
            raise util.Abort(_('review identifier must begin with bz://'))

        full = rid
        paths = rid[5:].split('/')
        if not paths[0]:
            raise util.Abort(_('review identifier must not be bz://'))

        bug = paths[0]
        if not bug.isdigit():
            raise util.Abort(_('first path component of review identifier must be a bug number'))
        self.bug = int(bug)

        if len(paths) > 1:
            self.user = paths[1]

        if len(paths) > 2:
            raise util.Abort(_('unrecognized review id: %s') % rid)

    def __nonzero__(self):
        if self.bug or self.user:
            return True

        return False

    @property
    def full(self):
        s = 'bz://%s' % self.bug
        if self.user:
            s += '/%s' % self.user

        return s

def pushcommand(orig, ui, repo, *args, **kwargs):
    """Wraps commands.push to read the --reviewid argument."""

    ReviewID(kwargs['reviewid'])

    # There isn't a good way to send custom arguments to the push api. So, we
    # inject some temporary values on the repo. This may fail in many
    # scenarios, most of them related to server operation.
    repo.noreviewboardpush = kwargs['noreview']
    repo.reviewid = kwargs['reviewid']

    try:
        return orig(ui, repo, *args, **kwargs)
    finally:
        repo.noreviewboardpush = None
        repo.reviewid = None

# kwargs is here for "bookmarks," which was introduced in Mercurial 3.2. We
# can add it explicitly once support for <3.2 has been dropped.
def wrappedpush(orig, repo, remote, force=False, revs=None, newbranch=False,
                **kwargs):
    """Wraps exchange.push to enforce restrictions for review pushes."""
    if not remote.capable('reviewboard'):
        return orig(repo, remote, force=force, revs=revs, newbranch=newbranch,
                    **kwargs)

    ircnick = repo.ui.config('mozilla', 'ircnick', None)
    if not ircnick:
        raise util.Abort(_('you must set mozilla.ircnick in your hgrc config '
            'file to your IRC nickname in order to perform code reviews'))

    # If no arguments are specified to push, Mercurial will try to push all
    # non-remote changesets by default. This can result in unexpected behavior,
    # especially for people doing multi-headed development.
    #
    # Since we reject pushes with multiple heads anyway, default to pushing
    # the working copy.
    if not revs:
        revs = [repo['.'].node()]

    # We filter the "extension isn't installed" message from the server.
    # This is a bit hacky, but it's easier than sending a signal over the
    # wire protocol (at least until bundle2).
    oldcls = remote.ui.__class__
    class filteringwrite(remote.ui.__class__):
        def write(self, *args, **kwargs):
            if args[0] == _('remote: ') and len(args) >= 2 and \
                args[1].startswith('REVIEWBOARD: '):
                return

            return oldcls.write(self, *args, **kwargs)

    remote.ui.__class__ = filteringwrite
    try:
        # We always do force push because we don't want users to need to
        # specify it. The big danger here is pushing multiple heads or
        # branches or mq patches. We check the former above and we don't
        # want to limit user choice on the latter two.
        return orig(repo, remote, force=True, revs=revs, newbranch=newbranch,
                **kwargs)
    finally:
        remote.ui.__class__ = oldcls

def wrappedpushbookmark(orig, pushop):
    """Wraps exchange._pushbookmark to also push a review."""
    result = orig(pushop)

    if not pushop.remote.capable('reviewboard'):
        return result

    ui = pushop.ui
    repo = pushop.repo

    if repo.noreviewboardpush:
        return result

    reviewnode = None
    if pushop.revs:
        reviewnode = repo[pushop.revs[-1]].node()
    elif pushop.outgoing.missing:
        reviewnode = pushop.outgoing.missing[-1]
    else:
        ui.write(_('Unable to determine what to review. Please invoke '
            'with -r to specify what to review.\n'))
        return result

    assert reviewnode

    doreview(repo, ui, pushop.remote, reviewnode)

    return result

def doreview(repo, ui, remote, reviewnode):
    """Do the work of submitting a review to a remote repo.

    :remote is a peerrepository.
    :reviewnode is the node of the tip to review.
    """
    assert remote.capable('reviewboard')

    bzauth = getbugzillaauth(ui)
    if not bzauth:
        ui.warn(_('Bugzilla credentials not available. Not submitting review.\n'))
        return

    # Given a tip node, we need to find all changesets to review.
    # A solution that works most of the time is to find all non-public
    # ancestors of that node.
    nodes = [reviewnode]
    for node in repo[reviewnode].ancestors():
        ctx = repo[node]
        if ctx.phase() == phases.public:
            break
        nodes.insert(0, ctx.node())

    # TODO need ability to manually override review nodes.

    identifier = None

    # The review identifier can come from a number of places. In order of
    # priority:
    # 1. --reviewid argument passed to push command
    # 2. The active bookmark
    # 3. The active branch (if it isn't default)
    # 4. A bug number extracted from commit messages

    if repo.reviewid:
        identifier = repo.reviewid

    # TODO The server currently requires a bug number for the identifier.
    # Pull bookmark and branch names in once allowed.
    #elif repo._bookmarkcurrent:
    #    identifier = repo._bookmarkcurrent
    #elif repo.dirstate.branch() != 'default':
    #    identifier = repo.dirstate.branch()

    if not identifier:
        for node in nodes:
            ctx = repo[node]
            bugs = parse_bugs(ctx.description())
            if bugs:
                identifier = 'bz://%s' % bugs[0]
                break

    identifier = ReviewID(identifier)

    if not identifier:
        ui.write(_('Unable to determine review identifier. Review '
            'identifiers are extracted from commit messages automatically. '
            'Try to begin one of your commit messages with "Bug XXXXXX -"\n'))
        return

    # Append irc nick to review identifier.
    # This is an ugly workaround to a limitation in ReviewBoard. RB doesn't
    # really support changing the owner of a review. It is doable, but no
    # history is stored and this leads to faulty attribution. More details
    # in bug 1034188.
    if not identifier.user:
        ircnick = ui.config('mozilla', 'ircnick', None)
        identifier.user = ircnick

    if hasattr(repo, 'mq'):
        for patch in repo.mq.applied:
            if patch.node in nodes:
                ui.warn(_('You are using mq to develop patches. mq is '
                          'deprecated. Please develop with bookmarks or '
                          'use the shelve extension instead.\n'))
                break

    lines = [
        '1',
        'reviewidentifier %s' % urllib.quote(identifier.full),
    ]

    for p in ('username', 'password', 'userid', 'cookie'):
        if getattr(bzauth, p, None):
            lines.append('bz%s %s' % (p, urllib.quote(getattr(bzauth, p))))

    reviews = repo.reviews
    oldparentid = reviews.findparentreview(identifier=identifier.full)

    # Include obsolescence data so server can make intelligent decisions.
    obsstore = repo.obsstore
    for node in nodes:
        lines.append('csetreview %s' % hex(node))
        precursors = [hex(n) for n in obsolete.allprecursors(obsstore, [node])]
        lines.append('precursors %s %s' % (hex(node), ' '.join(precursors)))

    ui.write(_('submitting %d changesets for review\n') % len(nodes))

    res = remote._call('pushreview', data='\n'.join(lines))

    # All protocol versions begin with: <version>\n
    try:
        off = res.index('\n')
        version = int(res[0:off])

        if version != 1:
            raise util.Abort(_('do not know how to handle response from server.'))
    except ValueError:
        raise util.Abort(_('invalid response from server.'))

    assert version == 1
    lines = res.split('\n')[1:]

    newparentid = None
    nodereviews = {}
    reviewdata = {}

    for line in lines:
        t, d = line.split(' ', 1)

        if t == 'display':
            ui.write('%s\n' % d)
        elif t == 'error':
            raise util.Abort(d)
        elif t == 'parentreview':
            newparentid = d
            reviews.addparentreview(identifier.full, newparentid)
            reviewdata[newparentid] = {}
        elif t == 'csetreview':
            node, rid = d.split(' ', 1)
            node = bin(node)
            reviews.addnodereview(node, rid, newparentid)
            reviewdata[rid] = {}
            nodereviews[node] = rid
        elif t == 'reviewdata':
            rid, field, value = d.split(' ', 2)
            value = urllib.unquote(value)
            reviewdata[rid][field] = value
        elif t == 'rburl':
            reviews.baseurl = d

    reviews.remoteurl = remote.url()

    reviews.write()
    for rid, data in reviewdata.iteritems():
        reviews.savereviewrequest(rid, data)

    ui.write('\n')
    for node in nodes:
        rid = nodereviews[node]
        ctx = repo[node]
        # Bug 1065024 use cmdutil.show_changeset() here.
        ui.write('changeset:  %s:%s\n' % (ctx.rev(), ctx.hex()[0:12]))
        ui.write('summary:    %s\n' % ctx.description().splitlines()[0])
        ui.write('review:     %s' % reviews.reviewurl(rid))
        if reviewdata[rid].get('status') == 'pending':
            ui.write(' (pending)')
        ui.write('\n\n')

    ui.write(_('review id:  %s\n') % identifier.full)
    ui.write(_('review url: %s') % reviews.parentreviewurl(identifier.full))
    if reviewdata[newparentid].get('status', None) == 'pending':
        ui.write(' (pending)')
    ui.write('\n')

def _pullreviews(repo):
    reviews = repo.reviews
    if not reviews.remoteurl:
        raise util.Abort(_("We don't know of any review servers. Try "
                           "creating a review first."))

    reviewdata = _pullreviewidentifiers(repo, sorted(reviews.identifiers))
    repo.ui.write(_('updated %d reviews\n') % len(reviewdata))

def _pullreviewidentifiers(repo, identifiers):
    """Pull down information for a list of review identifier strings.

    This will request the currently published data for a review identifier,
    including the mapping of commits to review request ids for all review
    requests that are currently part of the identifier.
    """
    reviews = repo.reviews

    # In the ideal world, we'd use RBTools to talk directly to the ReviewBoard
    # API. Unfortunately, the Mercurial distribution on Windows doesn't ship
    # with the json module. So, we proxy through the Mercurial server and have
    # it do all the heavy lifting.
    # FUTURE Hook up RBTools directly.
    remote = hg.peer(repo, {}, reviews.remoteurl)
    remote.requirecap('pullreviews', _('obtain code reviews'))

    lines = ['1']
    for identifier in identifiers:
        lines.append('reviewid %s' % identifier)

    res = remote._call('pullreviews', data='\n'.join(lines))

    version = _verifyresponseversion(res)
    assert version == 1

    lines = res.split('\n')[1:]
    reviewdata = {}

    for line in lines:
        t, d = line.split(' ', 1)

        if t == 'parentreview':
            identifier, parentid = map(urllib.unquote, d.split(' ', 2))
            reviewdata[parentid] = {}
        elif t == 'csetreview':
            parentid, node, rid = map(urllib.unquote, d.split(' ', 3))
            reviewdata[rid] = {}
        elif t == 'reviewdata':
            rid, field, value = map(urllib.unquote, d.split(' ', 3))
            reviewdata.setdefault(rid, {})[field] = value
        else:
            raise util.Abort(_('unknown value in response payload: %s') % t)

    for rid, data in reviewdata.iteritems():
        reviews.savereviewrequest(rid, data)

    return reviewdata

def _verifyresponseversion(res):
    """Verify the format and version of a response from a server."""
    # Empty responses consist of a single line without a newline.
    try:
        off = res.index('\n')
    except ValueError:
        off = len(res)

    try:
        version = int(res[0:off])

        if version != 1:
            raise util.Abort(_('do not know how to handle response from server.'))
    except ValueError:
        raise util.Abort(_('invalid response from server.'))

    return version

class identifierrecord(object):
    """Describes a review identifier in the context of the store."""
    def __init__(self, parentrrid):
        """Create a new review identifier record.

        ``parentrrid`` is the review request id of the parent review for this
        review identifier.
        """
        self.parentrrid = parentrrid

class noderecord(object):
    """Describes a node in the context of the store."""
    def __init__(self, rrids=None, parentrrids=None):
        self.rrids = set()
        self.parentrrids = set()
        if rrids:
            self.rrids |= set(rrids)
        if parentrrids:
            self.parentrrids |= set(parentrrids)

class reviewstore(object):
    """Holds information about ongoing reviews.

    When we push and pull review information, we store that data in a local
    data store. This class interacts with that store.

    The file consists of newline delimited data. Each line begins with a
    data type followed by a space followed by the data for that type.
    The types are as follows:

    'u' - URL of the Review Board server associated with the reviews repository.

    'r' - The push path of the reviews repository.

    'p' - Maps review identifier to id of the associated parent review request.
          Format is "<identifier> <review-request-id>".

    'c' - Maps node to associated review request id. Format is
          "<node> <review-request-id>".

    'pc' - Maps node to review request id of the parent review request. This
           associates a commit to a specific review identifier. Format is
           "<node> <review-request-id>".
    """
    def __init__(self, repo):
        self._repo = repo
        self._vfs = scmutil.vfs(repo.vfs.join('reviewboard'), audit=False)

        # Maps review identifiers to identifierrecord instances.
        self._identifiers = {}
        # Maps parent review id to identifierrecord instances. Shares the same
        # object instances as _identifiers.
        self._prids = {}

        # Maps nodes to noderecord instances.
        self._nodes = {}

        self.baseurl = None
        self.remoteurl = None

        try:
            for line in repo.vfs('reviews'):
                line = line.strip()
                if not line:
                    continue

                fields = line.split(' ', 1)
                if len(fields) != 2:
                    repo.ui.warn(_('malformed line in reviews file: %r\n') %
                                   line)
                    continue

                t, d = fields

                # Identifier to parent review ID.
                if t == 'p':
                    ident, rrid = d.split(' ', 1)
                    r = identifierrecord(parentrrid=rrid)
                    self._identifiers[ident] = r
                    self._prids[rrid] = r
                # Node to review id.
                elif t == 'c':
                    node, rid = d.split(' ', 1)
                    assert len(node) == 40
                    r = self._nodes.setdefault(bin(node), noderecord())
                    r.rrids.add(rid)
                # Node to parent id.
                elif t == 'pc':
                    node, pid = d.split(' ', 1)
                    assert len(node) == 40
                    self._nodes[bin(node)].parentrrids.add(pid)
                elif t == 'u':
                    self.baseurl = d
                elif t == 'r':
                    self.remoteurl = d

        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise

    @property
    def identifiers(self):
        """Returns a set of all known review identifiers."""
        return set(self._identifiers.keys())

    def write(self):
        """Write the reviews file back to disk."""
        repo = self._repo

        wlock = repo.wlock()
        try:
            f = repo.vfs('reviews', 'w', atomictemp=True)

            if self.baseurl:
                f.write('u %s\n' % self.baseurl)
            if self.remoteurl:
                f.write('r %s\n' % self.remoteurl)

            for ident, r in sorted(self._identifiers.iteritems()):
                f.write('p %s %s\n' % (ident, r.parentrrid))
            for node, r in sorted(self._nodes.iteritems()):
                for rid in sorted(r.rrids):
                    f.write('c %s %s\n' % (hex(node), rid))
                for pid in sorted(r.parentrrids):
                    f.write('pc %s %s\n' % (hex(node), pid))

            f.close()
        finally:
            wlock.release()

    def savereviewrequest(self, rid, data):
        """Save metadata about an individual review request."""

        path = self._vfs.join('review/%s.state' % rid)
        lines = []
        for k, v in sorted(data.iteritems()):
            lines.append('%s %s' % (k, urllib.quote(v)))

        self._vfs.write(path, '%s\n' % '\n'.join(lines))

    def getreviewrequest(self, rid):
        """Obtain metadata about a single review request."""
        path = self._vfs.join('review/%s.state' % rid)
        data = self._vfs.tryread(path)
        if not data:
            return None

        d = {}
        for line in data.splitlines():
            line = line.rstrip()
            if not line:
                continue

            k, v = line.split(' ', 1)
            d[k] = urllib.unquote(v)

        return d

    def addparentreview(self, identifier, rrid):
        """Record the existence of a parent review."""
        self._identifiers[identifier] = identifierrecord(parentrrid=rrid)

    def addnodereview(self, node, rid, pid):
        """Record the existence of a review against a single node."""
        assert len(node) == 20
        assert pid
        r = self._nodes.setdefault(node, noderecord())
        r.rrids.add(rid)
        r.parentrrids.add(pid)

    def findnodereviews(self, node):
        """Find all reviews associated with a node."""
        assert len(node) == 20

        r = self._nodes.get(node)
        if r and r.rrids:
            return r.rrids

        return set()

    def findparentreview(self, identifier=None):
        """Find a parent review given some data."""

        if identifier:
            r = self._identifiers.get(identifier, None)
            if r:
                return r.parentrrid

        return None

    def parentreviewurl(self, identifier):
        """Obtain the URL associated with the review for an identifier."""
        r = self._identifiers.get(identifier, None)
        if not r:
            return None

        return '%s/r/%s' % (self.baseurl, r.parentrrid)

    def reviewurl(self, rid):
        """Obtain the URL associated with a review id."""
        return '%s/r/%s' % (self.baseurl, rid)

def template_reviews(repo, ctx, revcache, **args):
    """:reviews: List. Objects describing each review for this changeset."""
    if 'reviews' not in revcache:
        reviews = []
        for rid in sorted(repo.reviews.findnodereviews(ctx.node())):
            r = repo.reviews.getreviewrequest(rid)
            # Bug 1065022 add parent review info to this data structure.
            reviews.append({
                'url': repo.reviews.reviewurl(rid),
                'status': r.get('status'),
            })

        revcache['reviews'] = reviews
    return templatekw.showlist('review', revcache['reviews'])

@command('pullreviews', [], _('hg pullreviews'))
def pullreviews(ui, repo, **opts):
    """Pull information about your active code reviews.

    When you initiate a code review by pushing to a review-enabled remote,
    your repository will track the existence of that code review.

    This command is used to pull code review information from a code review
    server into your local repository.
    """
    return _pullreviews(repo)

# The implementation of sshpeer.readerr() is buggy on Linux.
# See issue 4336 in Mercurial. This will likely get fixed in
# Mercurial 3.2. Work around it until we no longer support the
# buggy version.
def wrappedreaderr(orig, self):
    import fcntl
    flags = fcntl.fcntl(self.pipee, fcntl.F_GETFL)
    flags |= os.O_NONBLOCK
    oldflags = fcntl.fcntl(self.pipee, fcntl.F_SETFL, flags)

    chunks = []
    try:
        while True:
            try:
                s = self.pipee.read()
                if not s:
                    break
                chunks.append(s)
            except IOError:
                break
    finally:
        fcntl.fcntl(self.pipee, fcntl.F_SETFL, oldflags)

    for l in ''.join(chunks).splitlines():
        self.ui.status(_("remote: "), l, '\n')

def extsetup(ui):
    extensions.wrapfunction(exchange, 'push', wrappedpush)
    # _pushbookmark gets called near the end of push. Sadly, there isn't
    # a better place to hook that has access to the pushop.
    extensions.wrapfunction(exchange, '_pushbookmark', wrappedpushbookmark)

    if os.name == 'posix':
        extensions.wrapfunction(sshpeer.sshpeer, 'readerr', wrappedreaderr)

    # Define some extra arguments on the push command.
    entry = extensions.wrapcommand(commands.table, 'push', pushcommand)
    entry[1].append(('', 'noreview', False,
                     _('Do not perform a review on push.')))
    entry[1].append(('', 'reviewid', '', _('Review identifier')))

    templatekw.keywords['reviews'] = template_reviews

def reposetup(ui, repo):
    if not repo.local():
        return

    class reviewboardrepo(repo.__class__):
        @localrepo.repofilecache('reviews')
        def reviews(self):
            return reviewstore(self)

    repo.__class__ = reviewboardrepo
    repo.noreviewboardpush = False
    repo.reviewid = None

    def prepushoutgoinghook(local, remote, outgoing):
        if remote.capable('reviewboard'):
            if len(outgoing.missingheads) > 1:
                raise util.Abort(_('cannot push multiple heads to remote; limit '
                                   'pushed revisions using the -r argument.'))

    repo.prepushoutgoinghooks.add('reviewboard', prepushoutgoinghook)
