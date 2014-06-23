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
from mercurial import util
from mercurial import wireproto
from mercurial.i18n import _
from mercurial.node import bin, hex

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
REPO_ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
PYLIB = os.path.join(REPO_ROOT, 'pylib')

demandimport.disable()
try:
    from mozautomation.commitparser import parse_bugs
    import hgrb.shared
except ImportError:
    sys.path.insert(0, os.path.join(PYLIB, 'mozautomation'))
    sys.path.insert(0, OUR_DIR)

    from mozautomation.commitparser import parse_bugs
    import hgrb.shared
demandimport.enable()

testedwith = '3.0.1'

def pushcommand(orig, ui, repo, *args, **kwargs):
    """Wraps commands.push to read the --reviewid argument."""

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

def wrappedpush(orig, repo, remote, force=False, revs=None, newbranch=False):
    """Wraps exchange.push to enforce restrictions for review pushes."""
    if not remote.capable('reviewboard'):
        return orig(repo, remote, force=force, revs=revs, newbranch=newbranch)

    # We always do force push because we don't want users to need to
    # specify it. The big danger here is pushing multiple heads or
    # branches or mq patches. We check the former above and we don't
    # want to limit user choice on the latter two.
    return orig(repo, remote, force=True, revs=revs, newbranch=newbranch)

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
        assert len(pushop.revs) == 1
        reviewnode = repo[pushop.revs[0]].node()
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

    username, password = repo.reviewboardauth()
    if not username or not password:
        ui.write(_('Review Board extension not properly configured: '
            'missing authentication credentials. Please define '
            '"username" and "password" in the [reviewboard] section of '
            'your hgrc.\n'))
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
    elif repo._bookmarkcurrent:
        identifier = repo._bookmarkcurrent
    elif repo.dirstate.branch() != 'default':
        identifier = repo.dirstate.branch()

    if not identifier:
        for node in nodes:
            ctx = repo[node]
            bugs = parse_bugs(ctx.description())
            if bugs:
                identifier = 'bug%s' % bugs[0]
                break

    if not identifier:
        ui.write(_('Unable to determine review identifier. Review '
            'identifiers are extracted from commit messages automatically. '
            'Try to begin one of your commit messages with "Bug XXXXXX -"\n'))
        return

    if hasattr(repo, 'mq'):
        for patch in repo.mq.applied:
            if patch.node in nodes:
                ui.warn(_('You are using mq to develop patches. mq is '
                          'deprecated. Please develop with bookmarks or '
                          'use the shelve extension instead.\n'))
                break

    lines = [
        '1',
        'bzusername %s' % urllib.quote(username),
        'bzpassword %s' % urllib.quote(password),
        'reviewidentifier %s' % urllib.quote(identifier),
    ]

    reviews = repo.reviews
    oldparentid = reviews.findparentreview(identifier=identifier)
    oldreviews = {}
    for node in nodes:
        rid = reviews.findnodereview(node)
        data = hex(node)
        if rid:
            data += ' %s' % rid
            oldreviews[rid] = node
        lines.append('csetreview %s' % data)

    displayer = cmdutil.show_changeset(ui, repo, {
        'template': '{label("log.changeset", rev)}'
                    '{label("log.changeset", ":")}'
                    '{label("log.changeset", node|short)} '
                    '{label("log.summary", firstline(desc))}\n'})

    ui.write(_('identified %d changesets for review\n') % len(nodes))
    ui.write(_('review identifier: %s\n') % identifier)

    res = remote._call('reviewboard', data='\n'.join(lines))
    lines = res.split('\n')
    if len(lines) < 1:
        raise util.Abort(_('Unknown response from server.'))

    version = int(lines[0])
    if version != 1:
        raise util.Abort(_('Do not know how to handle response.'))

    newreviews = {}
    newparentid = None

    for line in lines[1:]:
        t, d = line.split(' ', 1)

        if t == 'display':
            ui.write('%s\n' % d)
        elif t == 'csetreview':
            node, rid = d.split(' ', 1)
            reviews.addnodereview(bin(node), rid)
            newreviews[rid] = bin(node)
        elif t == 'parentreview':
            newparentid = d
            reviews.addparentreview(identifier, newparentid)

    reviews.write()

    if not oldparentid:
        ui.write(_('created review request: %s\n' % newparentid))
    elif newparentid != oldparentid:
        assert 'This should never happen.'
    else:
        ui.write(_('updated review request: %s\n' % newparentid))

    if len(nodes) > 1:
        for rid, node in sorted(newreviews.iteritems()):
            ctx = repo[node]
            #displayer.show(ctx)

            if rid not in oldreviews:
                ui.write(_('created changeset review: %s\n') % rid)
            elif oldreviews[rid] != node:
                ui.write(_('updated changeset review: %s\n') % rid)

class reviewstore(object):
    """Holds information about ongoing reviews.

    When we push and pull review information, we store that data in a local
    file. This class manages that file.

    The file consists of newline delimited data. Each line begins with a
    data type followed by a space followed by the data for that type.
    The types are as follows:

    1 - Maps nodes to review ids. Format is "<node> <rid>" where <node>
        should be a hex node and <rid> should be an opaque identifier.
    """
    def __init__(self, repo):
        self._repo = repo

        # Maps nodes to review ids.
        self._nodes = {}
        # Maps identifiers to parent ids.
        self._parents = {}

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

                # Node to review id
                if t == 'c':
                    node, rid = d.split(' ', 1)
                    assert len(node) == 40
                    self._nodes[bin(node)] = rid
                elif t == 'p':
                    ident, rid = d.split(' ', 1)
                    self._parents[ident] = rid

        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise

    def write(self):
        """Write the reviews file back to disk."""
        repo = self._repo

        wlock = repo.wlock()
        try:
            f = repo.vfs('reviews', 'w', atomictemp=True)

            for ident, rid in sorted(self._parents.iteritems()):
                f.write('p %s %s\n' % (ident, rid))
            for node, rid in sorted(self._nodes.iteritems()):
                f.write('c %s %s\n' % (hex(node), rid))

            f.close()
        finally:
            wlock.release()

    def addparentreview(self, identifier, rid):
        """Record the existence of a parent review."""
        self._parents[identifier] = rid

    def addnodereview(self, node, rid):
        """Record the existence of a review against a single node."""
        assert len(node) == 20
        self._nodes[node] = rid

    def findnodereview(self, node):
        """Attempt to find a review for the specified changeset.

        We look for both direct review associations as well as obsolescence
        data to find reviews associated with precursor changesets.
        """
        assert len(node) == 20

        rid = self._nodes.get(node)
        if rid:
            return rid

        obstore = self._repo.obsstore
        for pnode in obsolete.allprecursors(obstore, [node]):
            rid = self._nodes.get(pnode, None)
            if rid:
                return rid

        return None

    def findparentreview(self, identifier=None):
        """Find a parent review given some data."""

        if identifier:
            rid = self._parents.get(identifier, None)
            if rid:
                return rid

        return None


def extsetup(ui):
    extensions.wrapfunction(exchange, 'push', wrappedpush)
    # _pushbookmark gets called near the end of push. Sadly, there isn't
    # a better place to hook that has access to the pushop.
    extensions.wrapfunction(exchange, '_pushbookmark', wrappedpushbookmark)

    # Define some extra arguments on the push command.
    entry = extensions.wrapcommand(commands.table, 'push', pushcommand)
    entry[1].append(('', 'noreview', False,
                     _('Do not perform a review on push.')))
    entry[1].append(('', 'reviewid', '', _('Review identifier')))

def reposetup(ui, repo):
    if not repo.local():
        return

    class reviewboardrepo(repo.__class__):
        def __init__(self, *args, **kwargs):
            super(reviewboardrepo, self).__init__(*args, **kwargs)

            self.noreviewboardpush = False
            self.reviewid = None

        def reviewboardauth(self):
            """Obtain the credentials to authenticate with ReviewBoard."""

            # TODO attempt to grab these from Firefox profile automatically.
            # See code in bzexport that does that.
            username = ui.config('reviewboard', 'username', None)
            password = ui.config('reviewboard', 'password', None)

            return username, password

        @localrepo.repofilecache('reviews')
        def reviews(self):
            return reviewstore(self)

    repo.__class__ = reviewboardrepo

    def prepushoutgoinghook(local, remote, outgoing):
        if len(outgoing.missingheads) > 1:
            raise util.Abort(_('cannot push multiple heads to remote; limit '
                               'pushed revisions using the -r argument.'))

    repo.prepushoutgoinghooks.add('reviewboard', prepushoutgoinghook)
