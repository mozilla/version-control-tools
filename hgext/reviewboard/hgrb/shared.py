# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import urllib
from StringIO import StringIO
from mercurial import mdiff
from mercurial import patch
from mercurial import wireproto

@wireproto.wireprotocommand('reviewboard', '*')
def reviewboard(repo, proto, args=None):
    proto.redirect()

    # HTTP and SSH behave differently here. In SSH, the data is
    # passed as an argument. In HTTP, the data is on a stream which
    # we need to read from.
    if not args:
        fp = StringIO()
        proto.getfile(fp)
        data = fp.getvalue()
        fp.close()
    else:
        data = args['data']

    lines = data.split('\n')
    if len(lines) < 1:
        return wireproto.pusherr(_('Invalid payload.'))

    version = int(lines[0])
    if version < 1:
        return wireproto.pusherr(_('Your reviewboard extension is out of date. '
            'Please pull and update your version-control-tools repo.'))
    elif version > 1:
        return wireproto.pusherr(_('Your reviewboard extension is newer than '
            'what the server supports. Please downgrade to a compatible '
            'version.'))

    if len(lines) != 5:
        return wireproto.pusherr(_('Unexpected payload to reviewboard '
            'command.'))

    version, username, password, nodes, identifier = lines
    username = urllib.unquote(username)
    password = urllib.unquote(password)
    nodes = nodes.split()
    identifier = urllib.unquote(identifier)

    diffopts = mdiff.diffopts(context=8, showfunc=True)

    commits = {
        'individual': [],
        'squashed': {}
    }

    parent_node = repo[nodes[0]].p1().node()
    for i, node in enumerate(nodes):
        ctx = repo[node]
        p1 = ctx.p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=node, opts=diffopts))
        if i != 0:
            parent_diff = ''.join(patch.diff(repo, node1=parent_node,
                node2=nodes[i-1], opts=diffopts))

        commits['individual'].append({
            'id': node[0:12],
            'message': ctx.description(),
            'diff': diff,
            'parent_diff': parent_diff,
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=parent_node,
        node2=nodes[-1], opts=diffopts))

    rburl = repo.ui.config('reviewboard', 'url', None)
    rbid = repo.ui.configint('reviewboard', 'repoid', None)

    # TODO hook up to actual RB API
    # post_reviews(rb_url, username, password, rbid, identifier, commits)
    return '\n'.join([
        '1',
        'display:This will get printed on the client',
    ])
