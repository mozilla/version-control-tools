# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board server extension

This extensions adds a custom wire protocol command to the server to receive
new review requests.

This extension requires configuration before it can work.

The [reviewboard] section in the hgrc must have the following:

* url - the string URL of the Review Board server to talk to.
* repoid - the integer repository ID of this repository in Review Board.

url is commonly defined in the global hgrc whereas repoid is repository
local.
"""

import urllib
from StringIO import StringIO

from mercurial import extensions
from mercurial import mdiff
from mercurial import patch
from mercurial import util
from mercurial import wireproto
from mercurial.i18n import _


def wireproto_reviewboard(repo, proto, *args, **kwargs):
    # Send output to client.
    proto.redirect()
    fp = StringIO()
    proto.getfile(fp)
    lines = fp.getvalue().split('\n')
    fp.close()

    if len(lines) != 4:
        return 'Unexpected payload\n'
        # TODO this hangs due to draining.
        return wireproto.pusherr('Unexpected payload to reviewboard command.')

    username, password, nodes, identifier = lines
    username = urllib.unquote(username)
    password = urllib.unquote(password)
    nodes = nodes.split()
    identifier = urllib.unquote(identifier)

    diffopts = mdiff.diffopts(context=8, showfunc=True, git=False)

    commits = {
        'individual': [],
        'squashed': {}
    }

    parent_node = repo[nodes[0]].p1().node()
    for i, node in enumerate(nodes):
        p1 = repo[node].p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=node, opts=diffopts))
        if i != 0:
            parent_diff = ''.join(patch.diff(repo, node1=parent_node,
                node2=nodes[i-1], opts=diffopts))

        commits['individual'].append({
            'id': node[0:12],
            'diff': diff,
            'parent_diff': parent_diff,
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=parent_node,
        node2=nodes[-1], opts=diffopts))

    rburl = repo.ui.config('reviewboard', 'url', None)
    rbid = repo.ui.configint('reviewboard', 'repoid', None)

    # TODO hook up to actual RB API
    # post_reviews(rb_url, username, password, rbid, identifier, commits)
    return 'This will get printed on the client\n'


def capabilities(orig, repo, proto):
    """Wraps wireproto.capabilities to advertise reviewboard support."""
    caps = orig(repo, proto)
    caps += ' reviewboard'
    return caps


def extsetup(ui):
    oldcap, args = wireproto.commands['capabilities']
    def newcapabilities(repo, proto):
        return capabilities(oldcap, repo, proto)
    wireproto.commands['capabilities'] = (newcapabilities, args)

    wireproto.commands['reviewboard'] = (wireproto_reviewboard, '')


def reposetup(ui, repo):
    if not repo.local():
        return

    if not ui.config('reviewboard', 'url', None):
        raise util.Abort(_('Please set reviewboard.url to the URL of the '
            'Review Board instance to talk to.'))

    if not ui.configint('reviewboard', 'repoid', None):
        raise util.Abort(_('Please set reviewboard.repoid to the numeric ID '
            'of the repository this repo is associated with.'))
