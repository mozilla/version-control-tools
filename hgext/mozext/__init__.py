# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""make Mozilla contributors more productive

This extension adds Mozilla-centric commands and functionality to Mercurial
to enable contributors to Firefox and related applications to be more
productive.

Included are commands that interface with Mozilla's automation infrastructure.
These allow developers to quickly check the status of repositories and builds
without having to leave the comfort of the terminal.

Known Mozilla Repositories
==========================

This extension teaches Mercurial about known Mozilla repositories.

Each main mozilla-central clone is given a common name. e.g. "mozilla-central"
becomes "central" and "mozilla-inbound" becomes "inbound." In addition,
repositories have short aliases to quickly refer to them. e.g.
"mozilla-central" is can be references by "m-c" or "mc."

The mechanism to resolve a repository string to a repository instance is
supplemented with these known aliases. For example, to pull from
mozilla-central, you can simply run `hg pull central`. There is no need to set
up the [paths] section in your hgrc!

To view the list of known repository aliases, run `hg moztrees`.

Unified Repositories
====================

Gecko code is developed in parallel across a number of repositories that are
cloned from the canonical repository, mozilla-central. Seasoned developers
typically interact with multiple repositories.

This extension provides mechanisms to create and maintain a single Mercurial
repository that contains changesets from multiple "upstream" repositories.

The recommended method to create a unified repository is to run `hg
cloneunified`. This will pull changesets from all major release branches and
mozilla-inbound.

Once you have a unified repository, you can pull changesets from repositories
by using `hg pull`, likely by specifying one of the tree aliases (see `hg
moztrees`).

One needs to be careful when pushing changesets when operating a unified
repository. By default, `hg push` will attempt to push all local changesets not
in a remote. This is obviously not desired (you wouldn't want to push
mozilla-central to mozilla-beta)! Instead, you'll want to limit outgoing
changesets to a specific head or revision. You can specify `hg push -r REV`.
Or, for your convenience, the `hg pushtree` is made available. By default, this
command will push the current "tip" revision to the tree specified. e.g. if you
have patches on the current tip that need to land in inbound, you can run
`hg pushtree inbound`.

You can also get creative and push a "remote tracking revision" to another
repository. e.g. `hg pushtree -r central/default inbound`.

Remote References
=================

When pulling from known Gecko repositories, this extension automatically
creates references to branches on the remote. These can be referenced via
the revision <tree>/<name>. e.g. 'central/default'.

Remote refs are read-only and are updated automatically during repository pull
and push operations.

This feature is similar to Git remote refs.

Static Analysis
===============

This extension provides static analysis to patches. Currently, only Python
style checking is performed.

To perform style checking for a single patch, run `hg critic`. By default,
this will analyze the current working directory. If the working directory is
clean, the tip changeset will be analyzed. By default, only changed lines are
reported on.

Static analysis is also performed automatically during qrefresh and commit
operations. To disable this behavior, add "noautocritic = True" to the
[mozext] section in your hgrc.

Pushlog Data
============

This extension supports downloading pushlog data from Mozilla's repositories.
Pushlog data records who pushed changesets where and when.

To use this functionality, you'll need to sync pushlog data from the server to
the local machine. This facilitates rapid data lookup and can be done by
running `hg pushlogsync`.

Once pushlog data is synced, you can use `hg changesetpushes` to look up push
information for a specific changeset.

Bug Info
========

Information about bugs is extracted from commit messages via the `hg bugsync`
command. Once information about bugs is extracted, you can look up information
about specific bugs via `hg buginfo`.
"""

import datetime
import errno
import os
import re
import shutil
import sys

from operator import methodcaller

from mercurial.i18n import _
from mercurial.commands import (
    push,
)
from mercurial.error import (
    RepoError,
)
from mercurial.localrepo import (
    repofilecache,
)
from mercurial.node import (
    hex,
)
from mercurial import (
    commands,
    cmdutil,
    demandimport,
    encoding,
    extensions,
    hg,
    util,
)

from mozautomation.changetracker import (
    ChangeTracker,
)

from mozautomation.repository import (
    MercurialRepository,
    RELEASE_TREES,
    REPOS,
    resolve_trees_to_official,
    resolve_trees_to_uris,
    resolve_uri_to_tree,
    tbpl_url,
)

import bzauth
import bz

bz_available = False

testedwith = '2.6.1 2.6.2 2.6.3'

commands.norepo += ' cloneunified moztrees treestatus'
cmdtable = {}
command = cmdutil.command(cmdtable)

colortable = {
    'buildstatus.success': 'green',
    'buildstatus.failed': 'red',
    'buildstatus.testfailed': 'cyan',
}


# Override peer path lookup such that common names magically get resolved to
# known URIs.
old_peerorrepo = hg._peerorrepo


def peerorrepo(ui, path, *args, **kwargs):
    # Always try the old mechanism first. That way if there is a local
    # path that shares the name of a magic remote the local path is accessible.
    try:
        return old_peerorrepo(ui, path, *args, **kwargs)
    except RepoError:
        tree, uri = resolve_trees_to_uris([path])[0]

        if not uri:
            raise

        path = uri
        return old_peerorrepo(ui, path, *args, **kwargs)

hg._peerorrepo = peerorrepo


def critique(ui, repo, entire=False, node=None, **kwargs):
    """Perform a critique of a changeset."""
    demandimport.disable()

    try:
        from flake8.engine import get_style_guide
    except ImportError:
        our_dir = os.path.dirname(__file__)
        for p in ('flake8', 'mccabe', 'pep8', 'pyflakes'):
            sys.path.insert(0, os.path.join(our_dir, p))

    from flake8.engine import get_style_guide
    from pep8 import DiffReport, parse_udiff

    style = get_style_guide(parse_argv=False, ignore='E128')

    if not entire:
        diff = ''.join(repo[node].diff())
        style.options.selected_lines = {}
        for k, v in parse_udiff(diff).items():
            if k.startswith('./'):
                k = k[2:]

            style.options.selected_lines[k] = v

        style.options.report = DiffReport(style.options)

    files = [f for f in repo[node].files() if f.endswith('.py')]
    style.check_files(files)

    demandimport.enable()


@command('moztrees', [], _('hg moztrees'))
def moztrees(ui, **opts):
    """Show information about Mozilla source trees."""
    from mozautomation.repository import TREE_ALIASES, REPOS

    longest = max(len(tree) for tree in REPOS.keys())
    ui.write('%s  %s\n' % (_('Repo').rjust(longest), _('Aliases')))

    for name in sorted(REPOS):
        aliases = []
        for alias, targets in TREE_ALIASES.items():
            if len(targets) > 1:
                continue

            if targets[0] == name:
                aliases.append(alias)

        ui.write('%s: %s\n' % (name.rjust(longest),
            ', '.join(sorted(aliases))))


@command('cloneunified', [], _('hg cloneunified [DEST]'))
def cloneunified(ui, dest='gecko', **opts):
    """Clone main Mozilla repositories into a unified local repository.

    This command will clone the most common Mozilla repositories and will
    add changesets and remote tracking markers into a common repository.

    If the destination path is not given, 'gecko' will be used.

    This command is effectively an alias for a number of other commands.
    However, due to the way Mercurial internally stores data, it is recommended
    to run this command to ensure optimal storage of data.
    """
    path = ui.expandpath(dest)
    repo = hg.repository(ui, path, create=True)

    success = False

    try:
        for tree in ('esr17', 'b2g18', 'release', 'beta', 'aurora', 'central',
            'inbound'):
            peer = hg.peer(ui, {}, tree)
            ui.warn('Pulling from %s.\n' % peer.url())
            repo.pull(peer)
        res = hg.update(repo, repo.lookup('central/default'))
        success = True
        return res
    finally:
        if not success:
            shutil.rmtree(path)


@command('pushtree',
    [('r', 'rev', 'tip', _('revision'), _('REV'))],
    _('hg pushtree [-r REV] TREE'))
def pushtree(ui, repo, tree=None, rev=None, **opts):
    """Push changesets to a Mozilla repository.

    If only the tree argument is defined, we will attempt to push the current
    tip to the repository specified. This may fail due to pushed mq patches,
    local changes, etc. Please note we only attempt to push the current tip and
    it's ancestors, not all changesets not in the remote repository. This is
    different from the default behavior of |hg push| and is the distinguishing
    difference from that command.

    If you would like to push a non-active head, specify it with -r REV. For
    example, if you are currently on mozilla-central but wish to push inbound
    to mozilla-inbound, run `hg pushtree -r inbound/default inbound`.
    """
    if not tree:
        raise util.Abort(_('A tree must be specified.'))

    tree, uri = resolve_trees_to_uris([tree], write_access=True)[0]

    if not uri:
        raise util.Abort("Don't know about tree: %s" % tree)

    return push(ui, repo, rev=[rev], dest=uri)


@command('treestatus', [], _('hg treestatus [TREE] ...'))
def treestatus(ui, *trees, **opts):
    """Show the status of the Mozilla repositories.

    If trees are open, it is OK to land code on them.

    If trees require approval, you'll need to obtain approval from
    release management to land changes.

    If trees are closed, you shouldn't push unless you are fixing the reason
    the tree is closed.
    """
    from mozautomation.treestatus import TreeStatusClient

    client = TreeStatusClient()
    status = client.all()

    trees = resolve_trees_to_official(trees)

    if trees:
        status = {k: status[k] for k in status if k in trees}

    longest = max(len(s) for s in status)

    for tree in sorted(status):
        s = status[tree]
        if s.status == 'closed':
            ui.write('%s: %s (%s)\n' % (tree.rjust(longest), s.status,
                s.reason))
        else:
            ui.write('%s: %s\n' % (tree.rjust(longest), s.status))


@command('tbpl', [], _('hg tbpl [TREE] [REV]'))
def tbpl(ui, repo, tree=None, rev=None, **opts):
    """Open TBPL showing build status for the specified revision.

    The command receives a tree name and a revision to query. The tree is
    required because a revision/changeset may existing in multiple
    repositories.
    """
    if not tree:
        raise util.Abort('A tree must be specified.')

    if not rev:
        raise util.Abort('A revision must be specified.')

    tree, repo_url = resolve_trees_to_uris([tree])[0]
    if not repo_url:
        raise util.Abort("Don't know about tree: %s" % tree)

    r = MercurialRepository(repo_url)
    node = repo[rev].hex()
    push = r.push_info_for_changeset(node)

    if not push:
        raise util.Abort("Could not find push info for changeset %s" % node)

    push_node = push.last_node

    url = tbpl_url(tree, push_node[0:12])

    import webbrowser
    webbrowser.get('firefox').open(url)


@command('critic',
    [('e', 'entire', False,
        _('Report on entire file content, not just changed parts'),
        ''
    )],
    _('hg critic [REV]')
)
def critic(ui, repo, rev='.', entire=False, **opts):
    """Perform a critique of a changeset.

    This will perform static analysis on a given changeset and report any
    issues found.
    """
    critique(ui, repo, node=rev, entire=entire, **opts)


@command('pushlogsync', [], _('hg pushlogsync'))
def syncpushinfo(ui, repo, tree=None, **opts):
    """Synchronize the pushlog information for all known Gecko trees.

    The pushlog info contains who, when, and where individual changesets were
    pushed.

    After running this command, you can query for push information for specific
    changesets.
    """
    for i, tree in enumerate(sorted(REPOS)):
        repo.changetracker.load_pushlog(tree)
        ui.progress('pushlogsync', i, total=len(REPOS))

    ui.progress('pushlogsync', None)


def print_changeset_pushes(ui, repo, rev, all=False):
    ctx = repo[rev]
    node = ctx.node()

    pushes = repo.changetracker.pushes_for_changeset(node)
    pushes = [p for p in pushes if all or p[0] in RELEASE_TREES]
    if not pushes:
        ui.warn('No pushes recorded for changeset: ', str(ctx), '\n')
        return 1

    longest_tree = max(len(p[0]) for p in pushes) + 2
    longest_user = max(len(p[3]) for p in pushes) + 2

    ui.write(ctx.rev(), ':', str(ctx), ' ', ctx.description(), '\n')

    ui.write('Release ', 'Tree'.ljust(longest_tree), 'Date'.ljust(20),
            'Username'.ljust(longest_user), 'Build Info\n')
    for tree, push_id, when, user, head_node in pushes:
        releases = set()
        release = ''
        versions = {}

        if tree == 'beta':
            versions = repo._beta_releases()
        elif tree == 'release':
            versions = repo._release_releases()

        for version, e in versions.items():
            vctx = repo[e[0]]
            if ctx.descendant(vctx):
                releases.add(version)

        if len(releases):
            release = sorted(releases)[0]

        tbpl = tbpl_url(tree, hex(head_node)[0:12])
        date = datetime.datetime.fromtimestamp(when)
        ui.write(release.ljust(8), tree.ljust(longest_tree), date.isoformat(),
            ' ', user.ljust(longest_user), tbpl or '', '\n')


@command('changesetpushes',
    [('a', 'all', False, _('Show all trees, not just release trees.'), '')],
    _('hg changesetpushes REV'))
def changesetpushes(ui, repo, rev, all=False, **opts):
    """Display pushlog information for a changeset.

    This command prints pushlog entries for a given changeset. It is used to
    answer the question: how did a changeset propagate to all the trees.
    """
    print_changeset_pushes(ui, repo, rev, all=all)


@command('bugsync', [], 'hg bugsync')
def syncbuginfo(ui, repo, **opts):
    """Synchronize bug info with the local database.

    This command must be performed before `hg buginfo` to ensure the data is up
    to date.
    """
    for rev in repo:
        ui.progress('changeset', rev, total=len(repo))
        ctx = repo[rev]

        bugs = repo._bugs_in_description(ctx.description())
        if not bugs:
            continue
        repo.changetracker.associate_bugs_with_changeset(bugs, ctx.node())

    ui.progress('changeset', None)


@command('buginfo',
    [('a', 'all', False, _('Show all trees, not just release trees.'), '')],
    _('hg buginfo [BUG] ...'))
def buginfo(ui, repo, *bugs, **opts):
    tracker = ChangeTracker(repo.join('changetracker.db'))

    nodes = set()
    for bug in bugs:
        nodes |= set(tracker.changesets_with_bug(bug))

    # Sorting by topological order would probably be preferred. This is quick
    # and easy.
    contexts = sorted([repo[node] for node in nodes], key=methodcaller('rev'))

    for ctx in contexts:
        print_changeset_pushes(ui, repo, ctx.rev(), all=opts['all'])
        ui.write('\n')


def critic_hook(ui, repo, node=None, **opts):
    critique(ui, repo, node=node, **opts)
    return 0


def pullexpand(orig, ui, repo, source='default', **opts):
    """Wraps built-in pull command to expand aliases to multiple sources."""
    for tree, uri in resolve_trees_to_uris([source]):
        result = orig(ui, repo, uri or tree, **opts)

        if result:
            return result

    return 0


class remoterefs(dict):
    """Represents a remote refs file."""

    def __init__(self, repo):
        dict.__init__(self)
        self._repo = repo

        try:
            for line in repo.vfs('remoterefs'):
                line = line.strip()
                if not line:
                    continue

                sha, ref = line.split(None, 1)
                ref = encoding.tolocal(ref)
                try:
                    self[ref] = repo.changelog.lookup(sha)
                except LookupError:
                    pass

        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def write(self):
        f = self._repo.vfs('remoterefs', 'w', atomictemp=True)
        for ref in sorted(self):
            f.write('%s %s\n' % (hex(self[ref]), encoding.fromlocal(ref)))
        f.close()


def extsetup(ui):
    global bz_available
    try:
        extensions.find('bzexport')
        bz_available = True
    except KeyError:
        pass

    extensions.wrapcommand(commands.table, 'pull', pullexpand)


def reposetup(ui, repo):
    """Custom repository implementation.

    Our custom repository class tracks remote tree references so users can
    reference specific revisions on remotes.
    """

    if not repo.local():
        return

    orig_findtags = repo._findtags
    orig_lookup = repo.lookup
    orig_pull = repo.pull
    orig_push = repo.push

    class remotestrackingrepo(repo.__class__):
        @repofilecache('remoterefs')
        def remoterefs(self):
            return remoterefs(self)

        @util.propertycache
        def changetracker(self):
            try:
                return ChangeTracker(self.join('changetracker.db'))
            except Exception as e:
                raise util.Abort(e.message)

        # Resolve remote ref symbols. For some reason, we need both lookup
        # and findtags implemented.
        def lookup(self, key):
            try:
                key = self.remoterefs[key]
            except (KeyError, TypeError):
                pass

            return orig_lookup(key)

        def _findtags(self):
            tags, tagtypes = orig_findtags()
            tags.update(self.remoterefs)

            return tags, tagtypes

        def pull(self, remote, *args, **kwargs):
            # Pulls from known repositories will automatically update our
            # remote tracking references.
            old_rev = len(self)
            res = orig_pull(remote, *args, **kwargs)
            lock = self.wlock()
            try:
                tree = resolve_uri_to_tree(remote.url())

                if tree:
                    self._update_remote_refs(remote, tree)
                    self.changetracker.load_pushlog(tree)

                # Sync bug info.
                for rev in self.changelog.revs(old_rev + 1):
                    ctx = self[rev]
                    bugs = self._bugs_in_description(ctx.description())
                    if bugs:
                        self.changetracker.associate_bugs_with_changeset(bugs,
                            ctx.node())

            finally:
                lock.release()

            return res

        def push(self, remote, *args, **kwargs):
            res = orig_push(remote, *args, **kwargs)
            lock = self.wlock()
            try:
                tree = resolve_uri_to_tree(remote.url())

                if tree:
                    self._update_remote_refs(remote, tree)

            finally:
                lock.release()

            return res

        def _update_remote_refs(self, remote, tree):
            for branch, nodes in remote.branchmap().items():
                for node in nodes:
                    self.remoterefs['%s/%s' % (tree, branch)] = node

            self.remoterefs.write()

        def _milestone_changesets(self):
            """Look up Gecko milestone changes.

            Returns a mapping of changeset node to milestone text.
            """
            m = {}

            for rev in self.file('config/milestone.txt'):
                ctx = self.filectx('config/milestone.txt', fileid=rev)

                lines = ctx.data().splitlines()
                lines = [l for l in lines if not l.startswith('#') and
                    l.strip()]

                if len(lines) != 1:
                    continue

                m[ctx.node()] = lines[0]

            return m

        def _beta_releases(self):
            """Obtain information for each beta release."""
            return self._release_versions('beta/')

        def _release_releases(self):
            return self._release_versions('release/')

        def _release_versions(self, prefix):
            d = {}

            for key, node in self.remoterefs.items():
                if not key.startswith(prefix):
                    continue

                key = key[len(prefix):]

                if not key.startswith('GECKO') or not key.endswith('RELBRANCH'):
                    continue

                version, date, _relbranch = key.split('_')
                version = version[5:]
                after = ''
                marker = ''

                if 'b' in version:
                    marker = 'b'
                    version, after = version.split('b')

                if len(version) > 2:
                    major, minor = version[0:2], version[2:]
                else:
                    major, minor = version

                version = '%s.%s' % (major, minor)
                if marker:
                    version += '%s%s' % (marker, after)

                d[version] = (key, node, major, minor, marker or None, after or None)

            return d

        BUG_RE = re.compile(r'''# bug followed by any sequence of numbers, or
                                # a standalone sequence of numbers
                             (
                               (?:
                                 bug |
                                 b= |
                                 # a sequence of 5+ numbers preceded by whitespace
                                 (?=\b\#?\d{5,}) |
                                 # numbers at the very beginning
                                 ^(?=\d)
                               )
                               (?:\s*\#?)(\d+)
                             )''', re.I | re.X)

        def _bugs_in_description(self, desc):
            return [int(m[1]) for m in self.BUG_RE.findall(desc)]

    repo.__class__ = remotestrackingrepo
    if not ui.configbool('mozext', 'noautocritic'):
        ui.setconfig('hooks', 'commit.critic', critic_hook)
        ui.setconfig('hooks', 'qrefresh.critic', critic_hook)
