# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import urllib
from StringIO import StringIO
from mercurial import mdiff
from mercurial import patch
from mercurial import wireproto

# TODO import this from final location so the symbol is defined.
def post_reviews(url, username, password, rbid, identifier, commits):
    pass

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

    # Note patch.diff() is appears to accept anything that can be fed into
    # repo[]. However, it blindly does a hex() on the argument as opposed
    # to the changectx, so we need to pass in the binary node.
    base_parent_node = repo[nodes[0]].p1().node()
    for i, node in enumerate(nodes):
        ctx = repo[node]
        p1 = ctx.p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=ctx.node(), opts=diffopts))
        if i:
            parent_diff = ''.join(patch.diff(repo, node1=base_parent_node,
                node2=repo[nodes[i-1]].node(), opts=diffopts))

        commits['individual'].append({
            'id': node[0:12],
            'message': ctx.description(),
            'diff': diff,
            'parent_diff': parent_diff,
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=base_parent_node,
        node2=repo[nodes[-1]].node(), opts=diffopts))

    rburl = repo.ui.config('reviewboard', 'url', None)
    rbid = repo.ui.configint('reviewboard', 'repoid', None)

    result = post_reviews(repo.ui.config('reviewboard', 'url'), username,
                          password, rbid, identifier, commits)
    return '\n'.join([
        '1',
        'display:This will get printed on the client',
        'reviewid:%s' % identifier,
    ])
