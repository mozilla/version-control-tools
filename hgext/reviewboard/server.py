# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board server extension

This extensions adds a custom wire protocol command to the server to receive
new review requests.

This extension requires configuration before it can work.

The [reviewboard] section in the hgrc must have the following:

* url - the string URL of the Review Board server to talk to.
* repoid - the integer repository ID of this repository in Review Board.
* username - the priveleged username used for special Review Board operations.
* password - the priveleged user account's password.

url is commonly defined in the global hgrc whereas repoid is repository
local.
"""

import os
import sys

from mercurial import (
    cmdutil,
    demandimport,
    extensions,
    hg,
    phases,
    pushkey,
    repair,
    util,
    wireproto,
)
from mercurial.i18n import _
from mercurial.node import (
    hex,
    nullid,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

demandimport.disable()
try:
    import hgrb.proto
except ImportError:
    sys.path.insert(0, OUR_DIR)
    import hgrb.proto
demandimport.enable()

testedwith = '3.3 3.4'

cmdtable = {}
command = cmdutil.command(cmdtable)


# Capabilities the server requires in clients.
requirecaps = set([
    # Client can speak protocol format 1.
    'proto1',
    # Client knows how to interpret lists in review data.
    'listreviewdata',
])


def capabilities(orig, repo, proto):
    """Wraps wireproto._capabilities to advertise reviewboard support."""
    caps = orig(repo, proto)

    # Old versions of the wire protocol exposed separate capabilities for each
    # feature. New versions expose a list of features in the "mozreview"
    # capability.
    #
    # We keep the old style around for a while until all clients have upgraded.
    reviewcaps = set()

    if repo.ui.configint('reviewboard', 'repoid', None):
        reviewcaps.add('pushreview')
        reviewcaps.add('pullreviews')
        reviewcaps.add('publish')

        # Deprecated.
        caps.append('reviewboard')
        caps.append('pullreviews')

    if repo.ui.config('reviewboard', 'isdiscoveryrepo', None):
        reviewcaps.add('listreviewrepos')

        # Deprecated.
        caps.append('listreviewrepos')

    if reviewcaps:
        caps.append('mozreview=%s' % ','.join(sorted(reviewcaps)))
        caps.append('mozreviewrequires=%s' % ','.join(sorted(requirecaps)))

    return caps


def changegrouphook(ui, repo, source, url, **kwargs):
    # We send output to *every* client that the reviewboard client
    # extension is required. The reviewboard client extension will
    # filter this output.
    repo.ui.write(
        _('REVIEWBOARD: You need to have the reviewboard client extension '
          'installed in order to perform code reviews.\n'))
    repo.ui.write(
        _('REVIEWBOARD: See https://hg.mozilla.org/hgcustom/version-control-tools/file/tip/hgext/reviewboard/README.rst\n'))


def disallowpushhook(ui, repo, **kwargs):
    repo.ui.write('Pushing to discovery repos is not allowed!\n')
    repo.ui.write('You likely are seeing this error because your '
                  '"reviewboard" Mercurial extension is out of date.\n')
    return 1


def pushstrip(repo, key, old, new):
    """pushkey for strip that allows remote stripping.

    We only allow users in a controlled users list to perform remote stripping.
    """
    if 'USER' not in os.environ:
        repo.ui.write(_('request not authenticated; cannot perform remote strip\n'))
        return 0

    allowed = repo.ui.configlist('reviewboard', 'remote_strip_users')
    if os.environ['USER'] not in allowed:
        repo.ui.write(_('user not in list of users allowed to remote strip\n'))
        return 0

    nodes = []
    for node in new.splitlines():
        ctx = repo[node]
        # Stripping changesets that are public carries too much risk that too
        # many children changesets will also get stripped. Disallow the
        # practice.
        if ctx.phase() == phases.public:
            repo.ui.write(_('cannot strip public changeset: %s\n') % ctx.hex())
            return 0

        nodes.append(ctx.node())

    # The strip extension does higher-level things like remove bookmarks
    # referencing stripped changesets. We shouldn't need this functionality, so
    # we use the core API.
    repair.strip(repo.ui, repo, nodes, backup=True, topic='remotestrip')
    return 1


def liststrip(repo):
    """listkeys for strip pushkey namespace."""
    # Namespace is push only, so nothing to return.
    return {}


def listreviewrepos(repo):
    """Obtains a mapping of available repositories to root node.

    The data is read from a file so as to incur minimal run-time overhead.
    """
    repos = {}
    for line in repo.vfs.tryreadlines('reviewrepos'):
        line = line.rstrip()
        if not line:
            continue

        node, url = line.split(None, 1)
        repos[url] = node

    return repos


def getreposfromreviewboard(repo):
    from reviewboardmods.pushhooks import ReviewBoardClient

    with ReviewBoardClient(repo.ui.config('reviewboard', 'url').rstrip('/')) as client:
        root = client.get_root()
        urls = set()

        repos = root.get_repositories(max_results=250, tool='Mercurial')
        try:
            while True:
                for r in repos:
                    urls.add(r.path)

                repos = repos.get_next()

        except StopIteration:
            pass

        return urls


@command('createrepomanifest', [
    ('-s', 'search', '', _('string to replace in URLs')),
    ('-r', 'replace', '', _('replacement string for URLs'))
    ],
    _('hg createrepomanifest'))
def createrepomanifest(ui, repo, search=None, replace=None):
    repos = {}
    for url in getreposfromreviewboard(repo):
        peer = hg.peer(ui, {}, url)
        root = peer.lookup('0')
        # Filter out empty repos.
        if root == nullid:
            continue

        if search and replace:
            url = url.replace(search, replace)

        repos[url] = root

    lines = []
    for url, root in sorted(repos.items()):
        lines.append('%s %s\n' % (hex(root), url))

    data = ''.join(lines)
    repo.vfs.write('reviewrepos', data)
    ui.write(data)


def extsetup(ui):
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)
    pushkey.register('strip', pushstrip, liststrip)

    # Add a pushkey namespace to obtain the list of available review
    # repositories. This is used for repository discovery.
    pushkey.register('reviewrepos', lambda *x: False, listreviewrepos)


def reposetup(ui, repo):
    if not repo.local():
        return

    if not ui.config('reviewboard', 'url', None):
        raise util.Abort(_('Please set reviewboard.url to the URL of the '
            'Review Board instance to talk to.'))

    if (not ui.configint('reviewboard', 'repoid', None) and
            not ui.configbool('reviewboard', 'isdiscoveryrepo')):
        raise util.Abort(_('Please set reviewboard.repoid to the numeric ID '
            'of the repository this repo is associated with.'))

    if not ui.config('reviewboard', 'username', None):
        raise util.Abort(_('Please set reviewboard.username to the username '
            'for priveleged communications with Review Board.'))

    if not ui.config('reviewboard', 'password', None):
        raise util.Abort(_('Please set reviewboard.password to the password '
            'for priveleged communications with Review Board.'))

    if not ui.config('bugzilla', 'url', None):
        raise util.Abort(_('Please set bugzilla.url to the URL of the '
            'Bugzilla instance to talk to.'))

    if ui.configbool('phases', 'publish', True):
        raise util.Abort(_('reviewboard server extension is only compatible '
            'with non-publishing repositories.'))

    ui.setconfig('hooks', 'changegroup.reviewboard', changegrouphook)

    if ui.configbool('reviewboard', 'isdiscoveryrepo'):
        ui.setconfig('hooks', 'pretxnchangegroup.disallowpush',
                     disallowpushhook)
