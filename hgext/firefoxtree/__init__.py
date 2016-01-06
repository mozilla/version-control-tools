# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""work with Firefox source repositories more easily.

The Firefox source repository is a collection of multiple repositories
all stemming from the same root commit. They can effectively be modeled
as a single, unified repository with multiple heads. This extension
facilitates doing that.

Remote Tracking Tags
====================

When you pull from a known Firefox repository, this extension will
automatically create a local-only tag corresponding to the name of
the remote repository.

For example, when you pull from https://hg.mozilla.org/mozilla-central,
the ``central`` tag will be created. You can then update to the last
pull mozilla-central changeset by running ``hg up central``.

These local tags are read only. If you update to a tag and commit, the
tag will not move forward.

Servers can optionally enable serving these tags by setting
``firefoxtree.servetags`` to True. When clients perform a pull, they will
download and apply these tags automatically.

Pre-defined Repository Paths
============================

Instead of defining URLs of Firefox repositories in your .hg/hgrc, the
extension defines them for you.

You can run `hg pull central` or `hg pull inbound` and the alias
automatically gets resolved to the appropriate URL.

The special source ``fxtrees`` will expand to the set of Firefox trees
that have previously been pulled. This is essentially an alias that runs
``hg pull`` in a loop.

If a source is a known alias that maps to multiple repositories (such as
``releases`` or ``integration``), all repositories in that alias are pulled.

The ``review`` path is also pre-defined to point to MozReview.

Safer Push Defaults
===================

The default behavior of `hg push` is to transfer all non-remote changesets
to the remote. For people with a head/bookmark-based workflow, this is
extremely annoying, as you'll perform the push only to have a hook on a
server reject it because you are pushing multiple heads.

This extension changes the default behavior of `hg push` to only push
'.' (the commit of the working copy) by default when pushing to a
Firefox repo.

This extension also prevents pushing of multiple heads to known Firefox
repos (the server would reject the multi-headed push anyway).

fxheads Command
===============

The `hg fxheads` command is a variation of `hg heads` that prints a concise
list of the last-known commits for the Firefox repositories.
"""

import os

from mercurial import (
    cmdutil,
    commands,
    exchange,
    extensions,
    hg,
    namespaces,
    revset,
    scmutil,
    templatekw,
    util,
    wireproto,
)
from mercurial.error import RepoError
from mercurial.i18n import _
from mercurial.node import (
    bin,
    hex,
)

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozautomation.repository import (
    MULTI_TREE_ALIASES,
    resolve_trees_to_uris,
    resolve_uri_to_tree,
)

testedwith = '3.3 3.4 3.5 3.6'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20firefoxtree'
# The root revisions in mozilla-central and comm-central, respectively.
MOZ_ROOT_REV = '8ba995b74e18334ab3707f27e9eb8f4e37ba3d29'
COMM_ROOT_REV = 'e4f4569d451a5e0d12a6aa33ebd916f979dd8faa'

cmdtable = {}
command = cmdutil.command(cmdtable)

shorttemplate = ''.join([
    '{label("log.changeset", rev)}',
    '{label("log.changeset", ":")}',
    '{label("log.changeset", node|short)}',
    ' ',
    '{label("log.tag", join(fxheads, " "))}',
    ' ',
    '{label("log.summary", firstline(desc))}',
    '\n',
    ])

def isfirefoxrepo(repo):
    """Whether a repository is a Firefox repository.

    A Firefox repository is a peer that has a URL of a known tree or a local
    repository whose initial commit is the well-known initial Firefox commit.
    """
    tree = resolve_uri_to_tree(repo.url())
    if tree:
        return True

    if len(repo) and repo[0].hex() in (MOZ_ROOT_REV, COMM_ROOT_REV):
        return True

    # Backdoor for testing.
    return repo.opener.exists('IS_FIREFOX_REPO')

# Wrap repo lookup to automagically resolve tree names to URIs.
def peerorrepo(orig, ui, path, *args, **kwargs):
    try:
        return orig(ui, path, *args, **kwargs)
    except RepoError:
        tree, uri = resolve_trees_to_uris([path])[0]
        if not uri:
            raise

        return orig(ui, uri, *args, **kwargs)

def share(orig, ui, source, *args, **kwargs):
    """Wraps hg.share to mark the firefoxtrees file as shared.

    The .hg/shared file lists things that are shared. We add firefoxtrees
    to it if we are a Firefox repo.
    """
    res = orig(ui, source, *args, **kwargs)

    # TODO Mercurial 3.7 introduces a standalone function that receives the
    # proper arguments so we can avoid this boilerplate.
    if isinstance(source, str):
        origsource = ui.expandpath(source)
        source, branches = hg.parseurl(origsource)
        srcrepo = hg.repository(ui, source)
    else:
        srcrepo = source.local()

    if not isfirefoxrepo(srcrepo):
        return res

    if args:
        dest = args[0]
    elif 'dest' in kwargs:
        dest = kwargs['dest']
    else:
        dest = None

    if not dest:
        dest = hg.defaultdest(source)
    else:
        dest = ui.expandpath(dest)

    destwvfs = scmutil.vfs(dest, realpath=True)
    r = hg.repository(ui, destwvfs.base)

    with r.vfs('shared', 'ab') as fh:
        fh.write('firefoxtrees\n')

    return res

# Wraps capabilities wireproto command to advertise firefoxtree existence.
def capabilities(orig, repo, proto):
    caps = orig(repo, proto)

    if isfirefoxrepo(repo) and \
            repo.ui.configbool('firefoxtree', 'servetags', False):
        caps.append('firefoxtrees')

    return caps


def _firefoxtreesrepo(repo):
    """Obtain a repo that can open the firefoxtrees file.

    Will return the passed ``repo`` in most cases. But if ``repo``
    is shared, we may return the repo from the share source.
    """
    shared = {s.strip() for s in repo.vfs.tryread('shared').splitlines()}

    if 'firefoxtrees' in shared and repo.sharedpath != repo.path:
        source = repo.vfs.split(repo.sharedpath)[0]
        srcurl, branches = hg.parseurl(source)
        return hg.repository(repo.ui, srcurl)
    else:
        return repo


def readfirefoxtrees(repo):
    """Read the firefoxtrees node mapping from the filesystem."""
    repo = _firefoxtreesrepo(repo)

    trees = {}
    data = repo.vfs.tryread('firefoxtrees')
    if not data:
        return trees

    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue

        tree, hexnode = line.split()
        trees[tree] = bin(hexnode)

    return trees


def writefirefoxtrees(repo):
    """Write the firefoxtrees node mapping to the filesystem."""
    lines = []
    trees = {}
    for tree, node in sorted(repo.firefoxtrees.items()):
        assert len(node) == 20
        lines.append('%s %s' % (tree, hex(node)))
        trees[tree] = hex(node)

    _firefoxtreesrepo(repo).vfs.write('firefoxtrees', '\n'.join(lines))

    # Old versions of firefoxtrees stored labels in the localtags file. Since
    # this file is read by Mercurial and has no relevance to us any more, we
    # prune relevant entries from this file so the data isn't redundant with
    # what we now write.
    localtags = repo.opener.tryread('localtags')
    havedata = len(localtags) > 0
    taglines  = []
    for line in localtags.splitlines():
        line = line.strip()
        node, tag = line.split()
        tree, uri = resolve_trees_to_uris([tag])[0]
        if not uri:
            taglines.append(line)

    if havedata:
        repo.vfs.write('localtags', '\n'.join(taglines))


def get_firefoxtrees(repo):
    """Generator for Firefox tree labels defined in this repository.

    Returns a tuple of (tag, node, tree, uri)
    """
    for tag, node in sorted(repo.firefoxtrees.items()):
        result = resolve_trees_to_uris([tag])[0]
        if not result[1]:
            continue
        tree, uri = result
        yield tag, node, tree, uri


@wireproto.wireprotocommand('firefoxtrees', '')
def firefoxtrees(repo, proto):
    lines = []

    for tag, node, tree, uri in get_firefoxtrees(repo):
        lines.append('%s %s' % (tag, hex(node)))

    return '\n'.join(lines)

def push(orig, repo, remote, force=False, revs=None, newbranch=False, **kwargs):
    # If no arguments are specified to `hg push`, Mercurial's default
    # behavior is to try to push all non-remote changesets. The Firefox
    # trees all have hooks that prevent new heads from being created.
    # This default Mercurial behavior can really cause problems when people
    # are doing multi-headed development (e.g. bookmark-based development
    # instead of mq). So, we silently change the default behavior of
    # `hg push` to only push the current changeset when pushing to a Firefox
    # repo.
    tree = resolve_uri_to_tree(remote.url())
    if tree and not revs:
        repo.ui.status(_('no revisions specified to push; '
            'using . to avoid pushing multiple heads\n'))
        revs = [repo['.'].node()]

    res = orig(repo, remote, force=force, revs=revs, newbranch=newbranch,
            **kwargs)

    # If we push to a known tree, update the remote refs.
    # We can ignore result of the push because updateremoterefs() doesn't care:
    # it merely synchronizes state with the remote. Worst case it is a no-op.
    if tree:
        updateremoterefs(repo, remote, tree.encode('utf-8'))

    return res

def prepushoutgoinghook(local, remote, outgoing):
    """Hook that prevents us from attempting to push multiple heads.

    Firefox repos have hooks that prevent receiving multiple heads. Waiting
    for the hook to fire on the remote wastes time. Implement it locally.
    """
    tree = resolve_uri_to_tree(remote.url())
    if not tree or tree == 'try':
        return

    if len(outgoing.missingheads) > 1:
        raise util.Abort(_('cannot push multiple heads to a Firefox tree; '
            'limit pushed revisions using the -r argument'))

def pull(orig, repo, remote, *args, **kwargs):
    old_rev = len(repo)
    res = orig(repo, remote, *args, **kwargs)

    if not isfirefoxrepo(repo):
        return res

    lock = repo.lock()
    try:
        if remote.capable('firefoxtrees'):
            lines = remote._call('firefoxtrees').splitlines()
            oldtags = {}
            for tag, node, tree, uri in get_firefoxtrees(repo):
                oldtags[tag] = node
            newtags = {}
            for line in lines:
                tag, node = line.split()
                newtags[tag] = node

                node = bin(node)

                if oldtags.get(tag, None) == node:
                    continue

                repo.firefoxtrees[tag] = node

                between = None
                if tag in oldtags:
                    between = len(list(repo.revs('%s::%s' % (
                        hex(oldtags[tag]), hex(node))))) - 1

                    if not between:
                        continue

                msg = _('updated firefox tree tag %s') % tag
                if between:
                    msg += _(' (+%d commits)') % between
                msg += '\n'
                repo.ui.status(msg)

            writefirefoxtrees(repo)

        tree = resolve_uri_to_tree(remote.url())
        if tree:
            tree = tree.encode('utf-8')
            updateremoterefs(repo, remote, tree)
    finally:
        lock.release()

    return res

def updateremoterefs(repo, remote, tree):
    """Update the remote refs for a Firefox repository.

    This is called during pull to create the remote tracking tags for
    Firefox repos.
    """
    # TODO Somehow the custom repo class is lost and the firefoxtrees attribute
    # isn't accessible. This is possibly a result of repo filter and/or clone
    # bundles interaction. See bug 1234396.
    if getattr(repo, 'firefoxtrees', None) is None:
        return

    # We only care about the default branch. We could import
    # RELBRANCH and other branches if we really cared about it.
    # Maybe later.
    branchmap = remote.branchmap()
    if 'default' not in branchmap:
        return

    # Firefox repos should only ever have a single head in the
    # default branch.
    defaultnodes = branchmap['default']
    node = defaultnodes[-1]

    repo.firefoxtrees[tree] = node
    writefirefoxtrees(repo)


def pullcommand(orig, ui, repo, source='default', **opts):
    """Wraps built-in pull command to expand special aliases."""
    if not isfirefoxrepo(repo):
        return orig(ui, repo, source=source, **opts)

    # The special source "fxtrees" will pull all trees we've pulled before.
    if source == 'fxtrees':
        for tag, node, tree, uri in get_firefoxtrees(repo):
            res = orig(ui, repo, source=tree, **opts)
            if res:
                return res

        return 0
    elif source in MULTI_TREE_ALIASES:
        for tree, uri in resolve_trees_to_uris([source]):
            res = orig(ui, repo, source=tree, **opts)
            if res:
                return res

        return 0

    return orig(ui, repo, source=source, **opts)

def outgoingcommand(orig, ui, repo, dest=None, **opts):
    """Wraps command.outgoing to limit considered nodes.

    We wrap commands.outgoing rather than hg._outgoing because the latter is a
    low-level API used by discovery. Manipulating it could lead to unintended
    consequences.
    """
    tree, uri = resolve_trees_to_uris([dest])[0]
    rev = opts.get('rev')
    if uri and not rev:
        ui.status(_('no revisions specified; '
            'using . to avoid inspecting multiple heads\n'))
        opts['rev'] = '.'

    return orig(ui, repo, dest=dest, **opts)

def pushcommand(orig, ui, repo, dest=None, **opts):
    """Wraps commands.push to resolve names to tree URLs.

    Ideally we'd patch ``ui.expandpath()``. However, It isn't easy to tell
    from that API whether we should be giving out HTTP or SSH URLs.
    This was proposed and rejected as a core feature to Mercurial.
    http://www.selenic.com/pipermail/mercurial-devel/2014-September/062052.html
    """
    if isfirefoxrepo(repo):
        # Automatically define "review" unless it is already defined.
        if dest == 'review':
            if not ui.config('paths', 'review', None):
                dest = 'ssh://reviewboard-hg.mozilla.org/gecko'
        else:
            tree, uri = resolve_trees_to_uris([dest], write_access=True)[0]
            if uri:
                dest = uri

    return orig(ui, repo, dest=dest, **opts)

@command('fxheads', [
    ('T', 'template', shorttemplate,
     _('display with template'), _('TEMPLATE')),
    ], _('show Firefox tree heads'))
def fxheads(ui, repo, **opts):
    """Show last known head commits for pulled Firefox trees.

    The displayed list may be out of date. Pull before running to ensure
    data is current.
    """
    if not isfirefoxrepo(repo):
        raise util.Abort(_('fxheads is only available on Firefox repos'))

    displayer = cmdutil.show_changeset(ui, repo, opts)
    seen = set()
    for tag, node, tree, uri in get_firefoxtrees(repo):
        if node in seen:
            continue
        seen.add(node)
        ctx = repo[node]
        displayer.show(ctx)

    displayer.close()

def fxheadsrevset(repo, subset, x):
    """``fxheads()``
    Last known head commits of pulled Firefox trees.
    """
    revset.getargs(x, 0, 0, _("fxheads takes no arguments"))
    r = revset.baseset(repo[node].rev()
                       for t, node, tr, u in get_firefoxtrees(repo))
    return r & subset


def _getcachedlabels(repo, ctx, cache):
    labels = cache.get('fxheads', None)
    if labels is None:
        if isfirefoxrepo(repo):
            labels = list(get_firefoxtrees(repo))
            cache['fxheads'] = labels
        else:
            labels = False
            cache['fxheads'] = False

    return labels


def template_fxheads(repo, ctx, templ, cache, **args):
    """:fxheads: List of strings. Firefox trees with heads on this commit."""
    labels = _getcachedlabels(repo, ctx, cache)
    if not labels:
        return []

    res = set(tag for tag, node, tree, uri in labels if node == ctx.node())

    return sorted(res)


def extsetup(ui):
    extensions.wrapfunction(hg, '_peerorrepo', peerorrepo)
    extensions.wrapfunction(hg, 'share', share)
    extensions.wrapfunction(exchange, 'push', push)
    extensions.wrapfunction(exchange, 'pull', pull)
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)
    extensions.wrapcommand(commands.table, 'outgoing', outgoingcommand)
    extensions.wrapcommand(commands.table, 'pull', pullcommand)
    extensions.wrapcommand(commands.table, 'push', pushcommand)
    revset.symbols['fxheads'] = fxheadsrevset

    keywords = {
        'fxheads': template_fxheads,
    }

    templatekw.keywords.update(keywords)

    # dockeywords was removed in 3.6.
    if hasattr(templatekw, 'dockeywords'):
        templatekw.dockeywords.update(keywords)


def reposetup(ui, repo):
    if not repo.local():
        return

    # Only change behavior on repositories that are clones of a Firefox
    # repository.
    if not isfirefoxrepo(repo):
        return

    repo.prepushoutgoinghooks.add('firefoxtree', prepushoutgoinghook)

    repo.firefoxtrees = readfirefoxtrees(repo)

    def listnames(r):
        return r.firefoxtrees.keys()

    def namemap(r, name):
        node = r.firefoxtrees.get(name)
        if node:
            return [node]
        return []

    def nodemap(r, node):
        return [name for name, n in r.firefoxtrees.iteritems()
                if n == node]

    n = namespaces.namespace('fxtrees',
                             templatename='fxtree',
                             listnames=listnames,
                             namemap=namemap,
                             nodemap=nodemap)

    repo.names.addnamespace(n)
