# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import urllib
from StringIO import StringIO
from mercurial import mdiff
from mercurial import patch
from mercurial import wireproto

# Wrap post_reviews because we don't want to require the clients to
# import rbtools.
def post_reviews(*args, **kwargs):
    from reviewboardmods.pushhooks import post_reviews as pr
    return pr(*args, **kwargs)

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

    bzusername = None
    bzpassword = None
    bzuserid = None
    bzcookie = None
    identifier = None
    nodes = []

    for line in lines[1:]:
        t, d = line.split(' ', 1)

        if t == 'bzusername':
            bzusername = urllib.unquote(d)
        elif t == 'bzpassword':
            bzpassword = urllib.unquote(d)
        elif t == 'bzuserid':
            bzuserid = urllib.unquote(d)
        elif t == 'bzcookie':
            bzcookie = urllib.unquote(d)
        elif t == 'reviewidentifier':
            identifier = urllib.unquote(d)
        elif t == 'csetreview':
            fields = d.split(' ', 1)
            if len(fields) > 1:
                nodes.append(tuple(fields))
            else:
                nodes.append((d, None))

    if not identifier:
        return wireproto.pusherr(_('no review identifier in request'))

    diffopts = mdiff.diffopts(context=8, showfunc=True)

    commits = {
        'individual': [],
        'squashed': {}
    }

    # Note patch.diff() is appears to accept anything that can be fed into
    # repo[]. However, it blindly does a hex() on the argument as opposed
    # to the changectx, so we need to pass in the binary node.
    base_parent_node = repo[nodes[0][0]].p1().node()
    for i, (node, rid) in enumerate(nodes):
        ctx = repo[node]
        p1 = ctx.p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=ctx.node(), opts=diffopts))
        if i:
            parent_diff = ''.join(patch.diff(repo, node1=base_parent_node,
                node2=repo[nodes[i-1][0]].node(), opts=diffopts))

        commits['individual'].append({
            'id': node,
            'rid': rid,
            'message': ctx.description(),
            'diff': diff,
            'parent_diff': parent_diff,
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=base_parent_node,
        node2=repo[nodes[-1][0]].node(), opts=diffopts))

    rburl = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    repoid = repo.ui.configint('reviewboard', 'repoid', None)

    parentrid, commitmap = post_reviews(rburl, repoid, identifier, commits,
                                        username=bzusername,
                                        password=bzpassword,
                                        cookie=bzcookie)

    lines = [
        '1',
        'rburl %s' % rburl,
        'reviewid %s' % identifier,
        'parentreview %s' % parentrid,
    ]

    for node, rid in commitmap.items():
        lines.append('csetreview %s %s' % (node, rid))

    return '\n'.join(lines)
