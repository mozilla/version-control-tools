# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Synchronize a foreign repository into a sub-directory of another.

``hg overlay`` is used to "overlay" the changesets of a remote,
unrelated repository into a sub-directory of another.
"""

from __future__ import absolute_import

import os
import shlex
import subprocess

from mercurial.i18n import _
from mercurial.node import bin, hex, short
from mercurial import (
    configitems,
    context,
    error,
    exchange,
    hg,
    registrar,
    revlog,
    scmutil,
    store,
    util,
)
from mercurial.utils import (
    dateutil,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

from mozhg.util import import_module

testedwith = b'4.7 4.8 4.9 5.0'
minimumhgversion = b'4.7'

cmdtable = {}

command = registrar.command(cmdtable)

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'overlay', b'sourceurl',
           default=configitems.dynamicdefault)

# TRACKING hg48
# parsemeta is now in storageutil
storageutil = import_module('mercurial.utils.storageutil')
if util.safehasattr(storageutil, 'parsemeta'):
    parsemeta = storageutil.parsemeta
else:
    parsemeta = revlog.parsemeta

REVISION_KEY = b'subtree_revision'
SOURCE_KEY = b'subtree_source'


def _ctx_summary(ctx):
    return [
        b'',
        _(b'changeset: %s') % ctx.hex(),
        _(b'user:      %s') % ctx.user(),
        _(b'date:      %s') % dateutil.datestr(ctx.date()),
        _(b'summary:   %s') % ctx.description().splitlines()[0],
    ]


def _summarise_changed(summary, repo_name, repo, last_ctx, prefix, files):
    overlaid_ctx = None
    all_ctxs = []
    matching_ctxs = []

    # Find revisions newer than the last overlaid.
    dest_revs = scmutil.revrange(
        repo, [b'%s:: and file("path:%s")' % (last_ctx.hex(), prefix)])
    for rev in dest_revs:
        ctx = repo[rev]

        if not overlaid_ctx:
            overlaid_ctx = ctx
            continue

        all_ctxs.append(ctx)

        # Report on revisions that touch problematic files.
        if files and (set(ctx.files()) & files):
            matching_ctxs.append(ctx)

    # No revisions to report.
    if not all_ctxs:
        return

    summary.extend([b'', _(b'%s Repository:') % repo_name,
                    b'', _(b'Last overlaid revision:')])
    summary.extend(_ctx_summary(overlaid_ctx))
    summary.extend([b'', _(b'Revisions that require investigation:')])

    # If we didn't find any revisions that match the problematic files report
    # on all revisions instead.
    for ctx in matching_ctxs if matching_ctxs else all_ctxs:
        summary.extend(_ctx_summary(ctx))


def _report_mismatch(ui, sourcerepo, lastsourcectx, destrepo, lastdestctx,
                     prefix, files, error_message, hint=None, notify=None):
    if notify:
        if files:
            prefixed_file_set = set(b'%s%s' % (prefix, f) for f in files)
        else:
            prefixed_file_set = set()

        summary = [error_message.rstrip()]
        _summarise_changed(summary, _(b'Source'), sourcerepo, lastsourcectx,
                           prefix, prefixed_file_set)
        _summarise_changed(summary, _(b'Destination'), destrepo, lastdestctx,
                           prefix, prefixed_file_set)
        summary_str = (b'%s\n' % b'\n'.join(summary))

        cmd = shlex.split(notify.decode('ascii'))
        cmd[0] = os.path.expanduser(os.path.expandvars(cmd[0]))
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            proc.communicate(summary_str)
        except OSError as ex:
            ui.write(b'notify command "%s" failed: %s\n' %
                     (cmd[0].encode('utf-8'), str(ex).encode('utf-8')))

    raise error.Abort(error_message, hint=hint)


def _verifymanifestsequal(ui, sourcerepo, sourcectx, destrepo, destctx,
                          prefix, lastsourcectx, lastdestctx, notify=None):
    assert prefix.endswith(b'/')

    sourceman = sourcectx.manifest()
    destman = destctx.manifest()

    sourcefiles = set(sourceman.keys())
    destfiles = set(p[len(prefix):] for p in destman if p.startswith(prefix))

    if sourcefiles ^ destfiles:
        _report_mismatch(
            ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
            destfiles ^ sourcefiles,
            (_(b'files mismatch between source and destination: %s')
             % b', '.join(sorted(destfiles ^ sourcefiles))),
            b'destination must match previously imported changeset (%s) exactly'
            % short(sourcectx.node()),
            notify=notify
        )

    # The set of paths is the same. Now verify the contents are identical.
    for sourcepath, sourcenode, sourceflags in sourceman.iterentries():
        destpath = b'%s%s' % (prefix, sourcepath)
        destnode, destflags = destman.find(destpath)

        if sourceflags != destflags:
            _report_mismatch(
                ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
                [sourcepath],
                (_(b'file flags mismatch between source and destination for '
                   b'%s: %s != %s') % (sourcepath, sourceflags or _(b'(none)'),
                                      destflags or _(b'(none)'))),
                notify=notify)

        # We can't just compare the nodes because they are derived from
        # content that may contain file paths in metadata, causing divergence
        # between the two repos. So we compare all the content in the
        # revisions.
        sourcefl = sourcerepo.file(sourcepath)
        destfl = destrepo.file(destpath)

        if sourcefl.read(sourcenode) != destfl.read(destnode):
            _report_mismatch(
                ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
                [sourcepath],
                _(b'content mismatch between source (%s) and destination (%s) '
                  b'in %s') % (short(sourcectx.node()), short(destctx.node()),
                              destpath),
                notify=notify)

        sourcetext = sourcefl.revision(sourcenode)
        desttext = destfl.revision(destnode)
        sourcemeta = parsemeta(sourcetext)[0]
        destmeta = parsemeta(desttext)[0]

        # Copy path needs to be normalized before comparison.
        if destmeta is not None and destmeta.get(b'copy', b'').startswith(prefix):
            destmeta[b'copy'] = destmeta[b'copy'][len(prefix):]

        # Copy revision may not be consistent across repositories because it
        # can be influenced by the path in a parent revision's copy metadata.
        # So ignore it.
        if sourcemeta and b'copyrev' in sourcemeta:
            del sourcemeta[b'copyrev']
        if destmeta and b'copyrev' in destmeta:
            del destmeta[b'copyrev']

        if sourcemeta != destmeta:
            _report_mismatch(
                ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
                [sourcepath],
                (_(b'metadata mismatch for file %s between source and dest: '
                   b'%s != %s') % (destpath, str(sourcemeta).encode('utf-8'), str(destmeta).encode('utf-8'))),
                notify=notify)


def _overlayrev(sourcerepo, sourceurl, sourcectx, destrepo, destctx,
                prefix):
    """Overlay a single commit into another repo."""
    assert prefix.endswith(b'/')
    assert len(sourcectx.parents()) < 2

    sourceman = sourcectx.manifest()

    def filectxfn(repo, memctx, path):
        sourcepath = path[len(prefix):]
        if sourcepath not in sourceman:
            return None

        node, flags = sourceman.find(sourcepath)
        sourcefl = sourcerepo.file(sourcepath)
        data = sourcefl.read(node)

        islink = b'l' in flags
        isexec = b'x' in flags

        copied = None
        renamed = sourcefl.renamed(node)
        if renamed:
            copied = b'%s%s' % (prefix, renamed[0])

        # TRACKING hg50 - `copied` renamed to `copysource`
        if util.versiontuple(n=2) >= (5, 0):
            return context.memfilectx(repo, memctx, path, data,
                                      islink=islink,
                                      isexec=isexec,
                                      copysource=copied)
        else:
            return context.memfilectx(repo, memctx, path, data,
                                      islink=islink,
                                      isexec=isexec,
                                      copied=copied)

    parents = [destctx.node(), None]
    files = [b'%s%s' % (prefix, f) for f in sourcectx.files()]
    extra = dict(sourcectx.extra())
    extra[REVISION_KEY] = sourcectx.hex()
    extra[SOURCE_KEY] = sourceurl

    memctx = context.memctx(destrepo, parents, sourcectx.description(),
                            files, filectxfn, user=sourcectx.user(),
                            date=sourcectx.date(), extra=extra)

    return memctx.commit()


def _dooverlay(sourcerepo, sourceurl, sourcerevs, destrepo, destctx, prefix,
               noncontiguous, notify=None):
    """Overlay changesets from one repository into another.

    ``sourcerevs`` (iterable of revs) from ``sourcerepo`` will effectively
    be replayed into ``destrepo`` on top of ``destctx``. File paths will be
    added to the directory ``prefix``.

    ``sourcerevs`` may include revisions that have already been overlayed.
    If so, overlay will resume at the first revision not yet processed.

    ``noncontigous`` removes the restriction that sourcerevs must be a
    contiguous DAG.
    """
    assert prefix
    prefix = prefix.rstrip(b'/') + b'/'

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
            if not noncontiguous:
                raise error.Abort(
                    _(b'source revisions must be part of contiguous DAG range'))

    if left:
        raise error.Abort(_(b'source revisions must be part of same DAG head'))

    sourcerevs = list(sourcerevs)

    sourcecl = sourcerepo.changelog
    allsourcehexes = set(hex(sourcecl.node(rev)) for rev in
                         sourcecl.ancestors([sourcerevs[-1]], inclusive=True))

    # Attempt to find an incoming changeset in dest and prune already processed
    # source revisions.
    lastsourcectx = None
    lastdestctx = None
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
            lastdestctx = ctx
            idx = sourcerevs.index(lastsourcectx.rev()) + 1
            ui.write(_(b'%s already processed as %s; '
                       b'skipping %d/%d revisions\n' %
                       (short(lastsourcectx.node()), short(ctx.node()),
                        idx, len(sourcerevs))))
            sourcerevs = sourcerevs[idx:]
            break
        except ValueError:
            # Else the changeset in the destination isn't in the incoming set.
            # This is OK iff the destination changeset is a conversion of
            # the parent of the first incoming changeset.
            # TODO: This assumption doesn't hold with noncontiguous=True
            firstsourcectx = sourcerepo[sourcerevs[0]]
            if firstsourcectx.p1().hex() == overlayed:
                break

            raise error.Abort(_(b'first source changeset (%s) is not a child '
                                b'of last overlayed changeset (%s)') % (
                short(firstsourcectx.node()), short(bin(overlayed))))

    if not sourcerevs:
        ui.write(_(b'no source revisions left to process\n'))
        return

    # We don't (yet) support overlaying merge commits.
    for rev in sourcerevs:
        ctx = sourcerepo[rev]
        if len(ctx.parents()) > 1:
            raise error.Abort(_(b'do not support overlaying merges: %s') %
                              short(ctx.node()))

    # If we previously performed an overlay, verify that changeset
    # continuity is uninterrupted.
    #
    # For the default mode of contiguous importing, we verify the last overlayed
    # changeset is the first parent of the first changeset to be overlayed. We
    # also verify that files in the destination match the last overlayed
    # changeset.
    #
    # For non-contiguous operation, we skip the parent check because it doesn't
    # make sense. For file comparisons, we check against the parent of the first
    # incoming changeset rather than the last overlayed changeset.
    #
    # The file content check ensures that repos don't get out of sync. They
    # ensure that diffs from the source repository match diffs in the
    # destination repository.
    if lastsourcectx:
        if not noncontiguous:
            if sourcerepo[sourcerevs[0]].p1() != lastsourcectx:
                raise error.Abort(_(b'parent of initial source changeset does '
                                    b'not match last overlayed changeset (%s)') %
                                  short(lastsourcectx.node()))

            comparectx = lastsourcectx
        else:
            comparectx = sourcerepo[sourcerevs[0]].p1()

        _verifymanifestsequal(ui, sourcerepo, comparectx, destrepo, destctx,
                              prefix, lastsourcectx, lastdestctx, notify)

    # All the validation is done. Proceed with the data conversion.
    with destrepo.lock():
        with destrepo.transaction(b'overlay'):
            for i, rev in enumerate(sourcerevs):
                ui.makeprogress(_(b'revisions'), i + 1, total=len(sourcerevs))
                sourcectx = sourcerepo[rev]
                node = _overlayrev(sourcerepo, sourceurl, sourcectx,
                                   destrepo, destctx, prefix)
                summary = sourcectx.description().splitlines()[0]
                ui.write(b'%s -> %s: %s\n' % (short(sourcectx.node()),
                                             short(node), summary))
                destctx = destrepo[node]

            ui.makeprogress(_(b'revisions'), None)


def _mirrorrepo(ui, repo, url):
    """Mirror a source repository into the .hg directory of another."""
    u = util.url(url)
    if u.islocal():
        raise error.Abort(_(b'source repo cannot be local'))

    # Remove scheme from path and normalize reserved characters.
    path = url.replace(b'%s://' % u.scheme, b'').replace(b'/', b'_')
    mirrorpath = repo.vfs.join(store.encodefilename(path))

    peer = hg.peer(ui, {}, url)
    mirrorrepo = hg.repository(ui, mirrorpath,
                               create=not os.path.exists(mirrorpath))

    missingheads = [head for head in peer.heads() if head not in mirrorrepo]
    if missingheads:
        ui.write(_(b'pulling %s into %s\n' % (url, mirrorpath)))
        exchange.pull(mirrorrepo, peer)

    return mirrorrepo


@command(b'overlay', [
    (b'd', b'dest', b'', _(b'destination changeset on top of which to overlay '
                        b'changesets')),
    (b'', b'into', b'', _(b'directory in destination in which to add files')),
    (b'', b'noncontiguous', False, _(b'allow non continuous dag heads')),
    (b'', b'notify', b'', _(b'application to handle error notifications'))
], _(b'[-d REV] SOURCEURL [REVS]'))
def overlay(ui, repo, sourceurl, revs=None, dest=None, into=None,
            noncontiguous=False, notify=None):
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
      DAG range (Unless --noncontiguous is passed).
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

    This command supports sending human readable notifications in the event
    that an overlay failed. Set --notify to an command that handles delivery
    of these errors. The message will be piped to the command via STDIN.
    """
    # We could potentially support this later.
    if not into:
        raise error.Abort(_(b'--into must be specified'))

    if not revs:
        revs = b'all()'

    sourcerepo = _mirrorrepo(ui, repo, sourceurl)
    sourcerevs = scmutil.revrange(sourcerepo, [revs])

    if not sourcerevs:
        raise error.Abort(_(b'unable to determine source revisions'))

    if dest:
        destctx = scmutil.revsymbol(repo, dest)
    else:
        destctx = scmutil.revsymbol(repo, b'tip')

    # Backdoor for testing to force static URL.
    sourceurl = ui.config(b'overlay', b'sourceurl', sourceurl)

    _dooverlay(sourcerepo, sourceurl, sourcerevs, repo, destctx, into,
               noncontiguous, notify)
