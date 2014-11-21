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
    exchange,
    extensions,
    hg,
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
    resolve_trees_to_uris,
    resolve_uri_to_tree,
)

testedwith = '3.0 3.1 3.2'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial:%20firefoxtree'
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
    '{label("log.tag", tags)}',
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

# Wraps capabilities wireproto command to advertise firefoxtree existence.
def capabilities(orig, repo, proto):
    caps = orig(repo, proto)

    if isfirefoxrepo(repo) and \
            repo.ui.configbool('firefoxtree', 'servetags', False):
        caps.append('firefoxtrees')

    return caps

@wireproto.wireprotocommand('firefoxtrees', '')
def firefoxtrees(repo, proto):
    lines = []

    for tag, node in sorted(repo.tags().items()):
        if not resolve_trees_to_uris([tag])[0][1]:
            continue

        lines.append('%s %s' % (tag, hex(node)))

    return '\n'.join(lines)

def push(orig, repo, remote, force=False, revs=None, newbranch=False, **kwargs):
    # If no arguments are specified to `hg push`, Mercurial's default
    # behavior is to try to push all non-remote changesets. The Firefox
    # trees all have hooks that prevent new heads from being created.
    # This default Mercurial behavior can really cause problems when people
    # are doing multi-headed development (e.g. bookmark-based development
    # instead of mq). So, we silently change the default behavior of
    # `hg push` to only push the current changeset.
    if isfirefoxrepo(repo) and not revs:
        repo.ui.status(_('no revisions specified to push; '
            'using . to avoid pushing multiple heads\n'))
        revs = [repo['.'].node()]

    res = orig(repo, remote, force=force, revs=revs, newbranch=newbranch,
            **kwargs)

    # If we push to a known tree, update the remote refs.
    # We can ignore result of the push because updateremoterefs() doesn't care:
    # it merely synchronizes state with the remote. Worst case it is a no-op.
    tree = resolve_uri_to_tree(remote.url())
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
            oldtags = repo.tags()
            newtags = {}
            for line in lines:
                tag, node = line.split()
                newtags[tag] = node

                node = bin(node)

                if oldtags.get(tag, None) == node:
                    continue

                repo.tag(tag, node, message=None, local=True,
                        user=None, date=None)
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

            # repo.tag will produce multiple entries for a tag. Prune
            # the old ones.
            localdata = repo.opener.tryread('localtags')
            newlines = []
            for line in localdata.splitlines():
                line = line.strip()
                node, tag = line.split()

                if tag not in newtags or newtags[tag] != node:
                    continue

                newlines.append(line)
            if newlines:
                newlines.append('')
            if newlines:
                repo.opener.write('localtags', '\n'.join(newlines))

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
    repo.tag(tree, node, message=None, local=True, user=None, date=None)

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
    for tag, node in sorted(repo.tags().items()):
        if not resolve_trees_to_uris([tag])[0][1]:
            continue

        ctx = repo[node]
        displayer.show(ctx)

    displayer.close()

def extsetup(ui):
    extensions.wrapfunction(hg, '_peerorrepo', peerorrepo)
    extensions.wrapfunction(exchange, 'push', push)
    extensions.wrapfunction(exchange, 'pull', pull)
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)

def reposetup(ui, repo):
    if not repo.local():
        return

    # Only change behavior on repositories that are clones of a Firefox
    # repository.
    if not isfirefoxrepo(repo):
        return

    repo.prepushoutgoinghooks.add('firefoxtree', prepushoutgoinghook)
