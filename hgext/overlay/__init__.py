# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Synchronize a foreign repository into a sub-directory of another.

``hg overlay`` is used to "overlay" the changesets of a remote,
unrelated repository into a sub-directory of another.
"""

from __future__ import absolute_import

import inspect
import os
import shlex
import subprocess

from mercurial.i18n import _
from mercurial.node import bin, hex, short
from mercurial import (
    cmdutil,
    context,
    error,
    exchange,
    filelog,
    hg,
    registrar,
    scmutil,
    store,
    util,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.util import import_module

# TRACKING hg43
configitems = import_module('mercurial.configitems')

testedwith = '4.1 4.2 4.3 4.4 4.5'

cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)

# TRACKING hg43 Mercurial 4.3 introduced the config registrar. 4.4
# requires config items to be registered to avoid a devel warning.
if util.safehasattr(registrar, 'configitem'):
    configtable = {}
    configitem = registrar.configitem(configtable)

    configitem('overlay', 'sourceurl',
               default=configitems.dynamicdefault)

REVISION_KEY = 'subtree_revision'
SOURCE_KEY = 'subtree_source'


def _ctx_summary(ctx):
    return [
        '',
        _('changeset: %s') % ctx.hex(),
        _('user:      %s') % ctx.user(),
        _('date:      %s') % util.datestr(ctx.date()),
        _('summary:   %s') % ctx.description().splitlines()[0],
    ]


def _summarise_changed(summary, repo_name, repo, last_ctx, prefix, files):
    overlaid_ctx = None
    all_ctxs = []
    matching_ctxs = []

    # Find revisions newer than the last overlaid.
    dest_revs = scmutil.revrange(
        repo, ['%s:: and file("path:%s")' % (last_ctx.hex(), prefix)])
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

    summary.extend(['', _('%s Repository:') % repo_name,
                    '', _('Last overlaid revision:')])
    summary.extend(_ctx_summary(overlaid_ctx))
    summary.extend(['', _('Revisions that require investigation:')])

    # If we didn't find any revisions that match the problematic files report
    # on all revisions instead.
    for ctx in matching_ctxs if matching_ctxs else all_ctxs:
        summary.extend(_ctx_summary(ctx))


def _report_mismatch(ui, sourcerepo, lastsourcectx, destrepo, lastdestctx,
                     prefix, files, error_message, hint=None, notify=None):
    if notify:
        if files:
            prefixed_file_set = set('%s%s' % (prefix, f) for f in files)
        else:
            prefixed_file_set = set()

        summary = [error_message.rstrip()]
        _summarise_changed(summary, _('Source'), sourcerepo, lastsourcectx,
                           prefix, prefixed_file_set)
        _summarise_changed(summary, _('Destination'), destrepo, lastdestctx,
                           prefix, prefixed_file_set)
        summary_str = ('%s\n' % '\n'.join(summary))

        cmd = shlex.split(notify)
        cmd[0] = os.path.expanduser(os.path.expandvars(cmd[0]))
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            proc.communicate(summary_str)
        except OSError as ex:
            ui.write('notify command "%s" failed: %s\n' % (cmd[0], ex))

    raise error.Abort(error_message, hint=hint)


def _verifymanifestsequal(ui, sourcerepo, sourcectx, destrepo, destctx,
                          prefix, lastsourcectx, lastdestctx, notify=None):
    assert prefix.endswith('/')

    sourceman = sourcectx.manifest()
    destman = destctx.manifest()

    sourcefiles = set(sourceman.iterkeys())
    destfiles = set(p[len(prefix):] for p in destman if p.startswith(prefix))

    if sourcefiles ^ destfiles:
        _report_mismatch(
            ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
            destfiles ^ sourcefiles,
            (_('files mismatch between source and destination: %s')
             % ', '.join(sorted(destfiles ^ sourcefiles))),
            'destination must match previously imported changeset (%s) exactly'
            % short(sourcectx.node()),
            notify=notify
        )

    # The set of paths is the same. Now verify the contents are identical.
    for sourcepath, sourcenode, sourceflags in sourceman.iterentries():
        destpath = '%s%s' % (prefix, sourcepath)
        destnode, destflags = destman.find(destpath)

        if sourceflags != destflags:
            _report_mismatch(
                ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
                [sourcepath],
                (_('file flags mismatch between source and destination for '
                   '%s: %s != %s') % (sourcepath, sourceflags or _('(none)'),
                                      destflags or _('(none)'))),
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
                _('content mismatch between source (%s) and destination (%s) '
                  'in %s') % (short(sourcectx.node()), short(destctx.node()),
                              destpath),
                notify=notify)

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
            _report_mismatch(
                ui, sourcerepo, lastsourcectx, destrepo, lastdestctx, prefix,
                [sourcepath],
                (_('metadata mismatch for file %s between source and dest: '
                   '%s != %s') % (destpath, sourcemeta, destmeta)),
                notify=notify)


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

        islink = 'l' in flags
        isexec = 'x' in flags

        copied = None
        renamed = sourcefl.renamed(node)
        if renamed:
            copied = '%s%s' % (prefix, renamed[0])

        # TRACKING hg45 Mercurial 4.5 renamed memctx to changectx and made
        # the argument positional instead of named.
        spec = inspect.getargspec(context.memfilectx.__init__)

        if 'changectx' in spec.args:
            return context.memfilectx(repo, memctx, path, data,
                                      islink=islink,
                                      isexec=isexec,
                                      copied=copied)
        else:
            return context.memfilectx(repo, path, data,
                                      islink=islink,
                                      isexec=isexec,
                                      copied=copied,
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
            if not noncontiguous:
                raise error.Abort(
                    _('source revisions must be part of contiguous DAG range'))

    if left:
        raise error.Abort(_('source revisions must be part of same DAG head'))

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
            # TODO: This assumption doesn't hold with noncontiguous=True
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
                raise error.Abort(_('parent of initial source changeset does '
                                    'not match last overlayed changeset (%s)') %
                                  short(lastsourcectx.node()))

            comparectx = lastsourcectx
        else:
            comparectx = sourcerepo[sourcerevs[0]].p1()

        _verifymanifestsequal(ui, sourcerepo, comparectx, destrepo, destctx,
                              prefix, lastsourcectx, lastdestctx, notify)

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
    ('', 'noncontiguous', False, _('allow non continuous dag heads')),
    ('', 'notify', '', _('application to handle error notifications'))
], _('[-d REV] SOURCEURL [REVS]'))
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

    _dooverlay(sourcerepo, sourceurl, sourcerevs, repo, destctx, into,
               noncontiguous, notify)
