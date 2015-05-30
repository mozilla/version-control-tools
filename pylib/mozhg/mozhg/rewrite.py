# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Utility functions for rewriting changesets."""

from collections import OrderedDict

import mercurial.bookmarks as bookmarks
import mercurial.cmdutil as cmdutil
import mercurial.context as context
import mercurial.hg as hg
import mercurial.lock as lockmod
import mercurial.obsolete as obsolete
import mercurial.phases as phases
import mercurial.repair as repair
import mercurial.util as util


# Mercurial 3.5 renamed readcurrent to readactive.
def activebookmark(repo):
    if hasattr(bookmarks, 'readactive'):
        return bookmarks.readactive(repo)
    else:
        return bookmarks.readcurrent(repo)


def newparents(repo, ctx, revmap):
    """Obtain the parent nodes of a potentially rewritten changeset.

    Given a changeset and a mapping of old to rewritten integer revisions,
    return the new parents for that changeset, taking any previous rewriting
    into account.
    """
    p1rev = ctx.p1().rev()
    p2rev = ctx.p2().rev()

    p1rev = revmap.get(p1rev, p1rev)
    p2rev = revmap.get(p2rev, p2rev)

    p1node = repo[p1rev].node()
    p2node = repo[p2rev].node()

    return [p1node, p2node]


def preservefilectx(oldctx):
    """Factory for memctx callback to obtain a memfilectx for a path.

    memctx constructors take a function that will be called to produce
    memfilectx instances for each file changed in the commit. A common
    pattern when rewriting changesets is to preserve/copy file changes
    from the old changeset. This function returns a function suitable
    for preserving filectx data from a base changeset.
    """
    def filectxfn(repo, memctx, path):
        try:
            fctx = oldctx.filectx(path)

            # This wonky pattern is copied from memctx.__init__.
            copied = fctx.renamed()
            if copied:
                copied = copied[0]

            # isexec and islink didn't exist until Mercurial 3.2.
            islink = 'l' in fctx.flags()
            isexec = 'x' in fctx.flags()
            return context.memfilectx(repo, path, fctx.data(),
                                      islink=islink,
                                      isexec=isexec,
                                      copied=copied,
                                      memctx=memctx)
        except KeyError:
            return None

    return filectxfn


def replacechangesets(repo, oldnodes, createfn, backuptopic='replacing'):
    """Replace changesets with new versions.

    This is a generic function used to perform history rewriting.

    Given an iterable of input nodes, a function will be called which is
    expected to produce a new changeset to replace the input node. The
    function signature should be:

        def createfn(repo, ctx, revmap, copyfilectxfn):

    It is passed a repo, the changectx being rewritten, a map of old to new
    revisions that have been changed so far, and a function that can be used
    as the memctx callback for obtaining memfilectx when no file modifications
    are to be performed (a common pattern). The function should return an
    *uncommitted* memctx holding the new changeset info.

    We currently restrict that the createfn callback must return a new
    changeset and that no file changes may occur. Restricting file changes
    satisfies the requirements this function was invented for and keeps the
    implementation simple.

    After the memctx is obtained, it is committed. Children changesets are
    rebased automatically after all changesets have been rewritten.

    After the old to new mapping is obtained, bookmarks are moved and old
    changesets are made obsolete or stripped, depending on what is appropriate
    for the repo configuration.

    This function handles locking the repository and performing as many actions
    in a transaction as possible.

    Before any changes are made, we verify the state of the repo is sufficient
    for transformation to occur and abort otherwise.
    """
    repo = repo.unfiltered()

    # Validate function called properly.
    for node in oldnodes:
        if len(node) != 20:
            raise util.Abort('replacechangesets expects 20 byte nodes')

    uoldrevs = [repo[node].rev() for node in oldnodes]
    oldrevs = sorted(uoldrevs)
    if oldrevs != uoldrevs:
        raise util.Abort('must pass oldnodes in changelog order')

    # We may perform stripping and stripping inside a nested transaction
    # is a recipe for disaster.
    # currenttransaction was added in 3.3. Copy the implementation until we
    # drop 3.2 compatibility.
    if hasattr(repo, 'currenttransaction'):
        intrans = repo.currenttransaction()
    else:
        if repo._transref and repo._transref().running():
            intrans = True
        else:
            intrans = False

    if intrans:
        raise util.Abort('cannot call replacechangesets when a transaction '
                         'is active')

    # The revisions impacted by the current operation. This is essentially
    # all non-hidden children. We don't operate on hidden changesets because
    # there is no point - they are hidden and deemed not important.
    impactedrevs = list(repo.filtered('visible').revs('%ld::', oldrevs))

    # If we'll need to update the working directory, don't do anything if there
    # are uncommitted changes, as this could cause a giant mess (merge
    # conflicts, etc). Note the comparison against impacted revs, as children
    # of rewritten changesets will be rebased below.
    dirstaterev = repo[repo.dirstate.p1()].rev()
    if dirstaterev in impactedrevs:
        cmdutil.checkunfinished(repo)
        cmdutil.bailifchanged(repo)

    obsenabled = False
    if hasattr(obsolete, 'isenabled'):
        obsenabled = obsolete.isenabled(repo, 'createmarkers')
    else:
        obsenabled = obsolete._enabled

    def adjustphase(repo, tr, phase, node):
        # transaction argument added in Mercurial 3.2.
        try:
            phases.advanceboundary(repo, tr, phase, [node])
            phases.retractboundary(repo, tr, phase, [node])
        except TypeError:
            phases.advanceboundary(repo, phase, [node])
            phases.retractboundary(repo, phase, [node])

    nodemap = {}
    wlock, lock, tr = None, None, None
    try:
        wlock = repo.wlock()
        lock = repo.lock()
        tr = repo.transaction('replacechangesets')

        # Create the new changesets.
        revmap = OrderedDict()
        for oldnode in oldnodes:
            oldctx = repo[oldnode]

            # Copy revmap out of paranoia.
            newctx = createfn(repo, oldctx, dict(revmap),
                              preservefilectx(oldctx))

            if not isinstance(newctx, context.memctx):
                raise util.Abort('createfn must return a context.memctx')

            if oldctx == newctx:
                raise util.Abort('createfn must create a new changeset')

            newnode = newctx.commit()
            # Needed so .manifestnode() works, which memctx doesn't have.
            newctx = repo[newnode]

            # This makes the implementation significantly simpler as we don't
            # need to worry about merges when we do auto rebasing later.
            if oldctx.manifestnode() != newctx.manifestnode():
                raise util.Abort('we do not allow replacements to modify files')

            revmap[oldctx.rev()] = newctx.rev()
            nodemap[oldnode] = newnode

            # Do phase adjustment ourselves because we want callbacks to be as
            # dumb as possible.
            adjustphase(repo, tr, oldctx.phase(), newctx.node())

        # Children of rewritten changesets are impacted as well. Rebase as
        # needed.
        for rev in impactedrevs:
            # It was handled by createfn() or by this loop already.
            if rev in revmap:
                continue

            oldctx = repo[rev]
            if oldctx.p1().rev() not in revmap:
                raise util.Abort('unknown parent of child commit: %s' %
                                 oldctx.hex(),
                                 hint='please report this as a bug')

            parents = newparents(repo, oldctx, revmap)
            mctx = context.memctx(repo, parents, oldctx.description(),
                                  oldctx.files(), preservefilectx(oldctx),
                                  user=oldctx.user(), date=oldctx.date(),
                                  extra=oldctx.extra())
            status = oldctx.p1().status(oldctx)
            mctx.modified = lambda: status[0]
            mctx.added = lambda: status[1]
            mctx.removed = lambda: status[2]

            newnode = mctx.commit()
            revmap[rev] = repo[newnode].rev()
            nodemap[oldctx.node()] = newnode

            # Retain phase.
            adjustphase(repo, tr, oldctx.phase(), newnode)

            ph = repo.ui.config('phases', 'new-commit')
            try:
                repo.ui.setconfig('phases', 'new-commit', oldctx.phase(),
                                  'rewriting')
                newnode = mctx.commit()
                revmap[rev] = repo[newnode].rev()
            finally:
                repo.ui.setconfig('phases', 'new-commit', ph)

        # Move bookmarks to new nodes.
        bmchanges = []
        oldactivebookmark = activebookmark(repo)

        for oldrev, newrev in revmap.items():
            oldnode = repo[oldrev].node()
            for mark, bmnode in repo._bookmarks.items():
                if bmnode == oldnode:
                    bmchanges.append((mark, repo[newrev].node()))

        for mark, newnode in bmchanges:
            repo._bookmarks[mark] = newnode

        if bmchanges:
            repo._bookmarks.write()

        # Update references to rewritten MQ patches.
        if hasattr(repo, 'mq'):
            q = repo.mq
            for e in q.applied:
                if e.node in nodemap:
                    e.node = nodemap[e.node]
                    q.applieddirty = True

            # This no-ops if nothing is dirty.
            q.savedirty()

        # If obsolescence is enabled, obsolete the old changesets.
        if obsenabled:
            markers = []
            for oldrev, newrev in revmap.items():
                markers.append((repo[oldrev], (repo[newrev],)))
            obsolete.createmarkers(repo, markers)

        # Move the working directory to the new node, if applicable.
        wdirrev = repo['.'].rev()
        if wdirrev in revmap:
            hg.updaterepo(repo, repo[revmap[wdirrev]].node(), True)

        # The active bookmark is tracked by its symbolic name, not its
        # changeset. Since we didn't do anything that should change the
        # active bookmark, we shouldn't need to adjust it.
        if activebookmark(repo) != oldactivebookmark:
            raise util.Abort('active bookmark changed; '
                             'this should not occur!',
                             hint='please file a bug')

        tr.close()

        # Unless obsolescence is enabled, strip the old changesets.
        if not obsenabled:
            stripnodes = [repo[rev].node() for rev in revmap.keys()]
            repair.strip(repo.ui, repo, stripnodes, topic=backuptopic)

    finally:
        if tr:
            tr.release()
        lockmod.release(wlock, lock)

    return nodemap
