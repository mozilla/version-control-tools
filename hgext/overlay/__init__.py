# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Synchronize a foreign repository into a sub-directory of another.

``hg overlay`` is used to "overlay" the changesets of a remote,
unrelated repository into a sub-directory of another.
"""

from __future__ import absolute_import

import os

from mercurial.i18n import _
from mercurial.node import bin, hex, short
from mercurial import (
    cmdutil,
    context,
    error,
    exchange,
    filelog,
    hg,
    scmutil,
    store,
    util,
)


testedwith = '4.1 4.2'

cmdtable = {}
command = cmdutil.command(cmdtable)


REVISION_KEY = 'subtree_revision'
SOURCE_KEY = 'subtree_source'


def _verifymanifestsequal(sourcerepo, sourcectx, destrepo, destctx, prefix):
    assert prefix.endswith('/')

    sourceman = sourcectx.manifest()
    destman = destctx.manifest()

    sourcefiles = set(sourceman.iterkeys())
    destfiles = set(p[len(prefix):] for p in destman if p.startswith(prefix))

    if sourcefiles ^ destfiles:
        raise error.Abort(_('files mismatch between source and destiation: %s')
                          % _(', ').join(sorted(destfiles ^ sourcefiles)),
                          hint=_('destination must match previously imported '
                                 'changeset (%s) exactly') %
                               short(sourcectx.node()))

    # The set of paths is the same. Now verify the contents are identical.
    for sourcepath, sourcenode, sourceflags in sourceman.iterentries():
        destpath = '%s%s' % (prefix, sourcepath)
        destnode, destflags = destman.find(destpath)

        if sourceflags != destflags:
            raise error.Abort(_('file flags mismatch between source and '
                                'destination for %s: %s != %s') %
                              (sourcepath,
                               sourceflags or _('(none)'),
                               destflags or _('(none)')))

        # We can't just compare the nodes because they are derived from
        # content that may contain file paths in metadata, causing divergence
        # between the two repos. So we compare all the content in the
        # revisions.
        sourcefl = sourcerepo.file(sourcepath)
        destfl = destrepo.file(destpath)

        if sourcefl.read(sourcenode) != destfl.read(destnode):
            raise error.Abort(_('content mismatch between source (%s) '
                                'and destination (%s) in %s') % (
                short(sourcectx.node()), short(destctx.node()), destpath))

        sourcetext = sourcefl.revision(sourcenode)
        desttext = destfl.revision(destnode)
        sourcemeta = filelog.parsemeta(sourcetext)[0]
        destmeta = filelog.parsemeta(desttext)[0]

        # Copy path needs to be normalized before comparison.
        if destmeta is not None and destmeta.get('copy', '').startswith(prefix):
            destmeta['copy'] = destmeta['copy'][len(prefix):]

        # Copy revision may not be consistent across repositories because it
        # can be influenced by the path in a parent revision's copy metadata.
        # So ignore it.
        if sourcemeta and 'copyrev' in sourcemeta:
            del sourcemeta['copyrev']
        if destmeta and 'copyrev' in destmeta:
            del destmeta['copyrev']

        if sourcemeta != destmeta:
            raise error.Abort(_('metadata mismatch for file %s between source '
                                'and dest: %s != %s') % (
                                destpath, sourcemeta, destmeta))


def _overlayrev(sourcerepo, sourceurl, sourcectx, destrepo, destctx,
                prefix):
    """Overlay a single commit into another repo."""
    assert prefix.endswith('/')
    assert len(sourcectx.parents()) < 2

    sourceman = sourcectx.manifest()

    def filectxfn(repo, memctx, path):
        sourcepath = path[len(prefix):]
        if sourcepath not in sourceman:
            return None

        node, flags = sourceman.find(sourcepath)
        sourcefl = sourcerepo.file(sourcepath)
        data = sourcefl.read(node)

        copied = None
        renamed = sourcefl.renamed(node)
        if renamed:
            copied = '%s%s' % (prefix, renamed[0])

        return context.memfilectx(repo, path, data, islink='l' in flags,
                                  isexec='x' in flags, copied=copied,
                                  memctx=memctx)

    parents = [destctx.node(), None]
    files = ['%s%s' % (prefix, f) for f in sourcectx.files()]
    extra = dict(sourcectx.extra())
    extra[REVISION_KEY] = sourcectx.hex()
    extra[SOURCE_KEY] = sourceurl

    memctx = context.memctx(destrepo, parents, sourcectx.description(),
                            files, filectxfn, user=sourcectx.user(),
                            date=sourcectx.date(), extra=extra)

    return memctx.commit()


def _dooverlay(sourcerepo, sourceurl, sourcerevs, destrepo, destctx, prefix):
    """Overlay changesets from one repository into another.

    ``sourcerevs`` (iterable of revs) from ``sourcerepo`` will effectively
    be replayed into ``destrepo`` on top of ``destctx``. File paths will be
    added to the directory ``prefix``.

    ``sourcerevs`` may include revisions that have already been overlayed.
    If so, overlay will resume at the first revision not yet processed.
    """
    assert prefix
    prefix = prefix.rstrip('/') + '/'

    ui = destrepo.ui

    sourcerevs.sort()

    # Source revisions must be a contiguous, single DAG range.
    left = set(sourcerevs)
    left.remove(sourcerevs.last())
    for ctx in sourcerepo[sourcerevs.last()].ancestors():
        if not left:
            break

        try:
            left.remove(ctx.rev())
        except KeyError:
            raise error.Abort(_('source revisions must be part of contiguous '
                                'DAG range'))

    if left:
        raise error.Abort(_('source revisions must be part of same DAG head'))

    sourcerevs = list(sourcerevs)

    sourcecl = sourcerepo.changelog
    allsourcehexes = set(hex(sourcecl.node(rev)) for rev in
                         sourcecl.ancestors([sourcerevs[-1]], inclusive=True))

    # Attempt to find an incoming changeset in dest and prune already processed
    # source revisions.
    lastsourcectx = None
    for rev in sorted(destrepo.changelog.ancestors([destctx.rev()],
                      inclusive=True), reverse=True):
        ctx = destrepo[rev]
        overlayed = ctx.extra().get(REVISION_KEY)

        # Changesets that weren't imported or that didn't come from the source
        # aren't important to us.
        if not overlayed or overlayed not in allsourcehexes:
            continue

        lastsourcectx = sourcerepo[overlayed]

        # If this imported changeset is in the set scheduled for import,
        # we can prune it and all ancestors from the source set. Since
        # sourcerevs is sorted and is a single DAG head, we can simply find
        # the offset of the first seen rev and assume everything before
        # has been imported.
        try:
            idx = sourcerevs.index(lastsourcectx.rev()) + 1
            ui.write(_('%s already processed as %s; '
                       'skipping %d/%d revisions\n' %
                       (short(lastsourcectx.node()), short(ctx.node()),
                        idx, len(sourcerevs))))
            sourcerevs = sourcerevs[idx:]
            break
        except ValueError:
            # Else the changeset in the destination isn't in the incoming set.
            # This is OK iff the destination changeset is a conversion of
            # the parent of the first incoming changeset.
            firstsourcectx = sourcerepo[sourcerevs[0]]
            if firstsourcectx.p1().hex() == overlayed:
                break

            raise error.Abort(_('first source changeset (%s) is not a child '
                                'of last overlayed changeset (%s)') % (
                short(firstsourcectx.node()), short(bin(overlayed))))

    if not sourcerevs:
        ui.write(_('no source revisions left to process\n'))
        return

    # We don't (yet) support overlaying merge commits.
    for rev in sourcerevs:
        ctx = sourcerepo[rev]
        if len(ctx.parents()) > 1:
            raise error.Abort(_('do not support overlaying merges: %s') %
                              short(ctx.node()))

    # If we previously performed an overlay, verify that changeset
    # continuity is uninterrupted. We ensure the parent of the first source
    # changeset matches the last imported changeset and that the state of
    # files in the last imported changeset matches exactly the state of files
    # in the destination changeset. If these conditions don't hold, the repos
    # got out of sync. If we continued, the first overlayed changeset would
    # have a diff that didn't match the source repository. In other words,
    # the history wouldn't be accurate. So prevent that from happening.
    if lastsourcectx:
        if sourcerepo[sourcerevs[0]].p1() != lastsourcectx:
            raise error.Abort(_('parent of initial source changeset does not '
                                'match last overlayed changeset (%s)') %
                              short(lastsourcectx.node()))

        _verifymanifestsequal(sourcerepo, lastsourcectx, destrepo, destctx,
                              prefix)

    # All the validation is done. Proceed with the data conversion.
    with destrepo.lock():
        with destrepo.transaction('overlay'):
            for i, rev in enumerate(sourcerevs):
                ui.progress(_('revisions'), i + 1, total=len(sourcerevs))
                sourcectx = sourcerepo[rev]
                node = _overlayrev(sourcerepo, sourceurl, sourcectx,
                                   destrepo, destctx, prefix)
                summary = sourcectx.description().splitlines()[0]
                ui.write('%s -> %s: %s\n' % (short(sourcectx.node()),
                                             short(node), summary))
                destctx = destrepo[node]

            ui.progress(_('revisions'), None)


def _mirrorrepo(ui, repo, url):
    """Mirror a source repository into the .hg directory of another."""
    u = util.url(url)
    if u.islocal():
        raise error.Abort(_('source repo cannot be local'))

    # Remove scheme from path and normalize reserved characters.
    path = url.replace('%s://' % u.scheme, '').replace('/', '_')
    mirrorpath = repo.vfs.join(store.encodefilename(path))

    peer = hg.peer(ui, {}, url)
    mirrorrepo = hg.repository(ui, mirrorpath,
                               create=not os.path.exists(mirrorpath))

    missingheads = [head for head in peer.heads() if head not in mirrorrepo]
    if missingheads:
        ui.write(_('pulling %s into %s\n' % (url, mirrorpath)))
        exchange.pull(mirrorrepo, peer)

    return mirrorrepo


@command('overlay', [
    ('d', 'dest', '', _('destination changeset on top of which to overlay '
                        'changesets')),
    ('', 'into', '', _('directory in destination in which to add files')),
], _('[-d REV] SOURCEURL [REVS]'))
def overlay(ui, repo, sourceurl, revs=None, dest=None, into=None):
    """Integrate contents of another repository.

    This command essentially replays changesets from another repository into
    this one. Unlike a simple pull + rebase, the files from the remote
    repository are "overlayed" or unioned with the contents of the destination
    repository.

    The functionality of this command is nearly identical to what ``hg
    transplant`` provides. However, the internal mechanism varies
    substantially.

    There are currently several restrictions to what can be imported:

    * The imported changesets must be in a single DAG head
    * The imported changesets (as evaluated by ``REVS``) must be a contiguous
      DAG range.
    * Importing merges is not supported.
    * The state of the files in the destination directory/changeset must
      exactly match the last imported changeset.

    That last point is important: it means that this command can effectively
    only be used for unidirectional syncing. In other words, the source
    repository must be the single source of all changes to the destination
    directory.

    The restriction of states being identical is to ensure that changesets
    in the source and destination are as similar as possible. For example,
    if the file content in the destination did not match the source, then
    the ``hg diff`` output for the next overlayed changeset would differ from
    the source.
    """
    # We could potentially support this later.
    if not into:
        raise error.Abort(_('--into must be specified'))

    if not revs:
        revs = 'all()'

    sourcerepo = _mirrorrepo(ui, repo, sourceurl)
    sourcerevs = scmutil.revrange(sourcerepo, [revs])

    if not sourcerevs:
        raise error.Abort(_('unable to determine source revisions'))

    if dest:
        destctx = repo[dest]
    else:
        destctx = repo['tip']

    # Backdoor for testing to force static URL.
    sourceurl = ui.config('overlay', 'sourceurl', sourceurl)

    _dooverlay(sourcerepo, sourceurl, sourcerevs, repo, destctx, into)
