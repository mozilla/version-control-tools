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

def getpayload(proto, args):
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

    return data

def parsepayload(proto, args):
    data = getpayload(proto, args)

    try:
        off = data.index('\n')
        version = int(data[0:off])

        if version < 1:
            return wireproto.pusherr(_('Your reviewboard extension is out '
                'of date. Please pull and update your version-control-tools '
                'repo.'))
        elif version > 1:
            return wireproto.pusherr(_('Your reviewboard extension is newer '
                'than what the server supports. Please downgrade to a '
                'compatible version.'))
    except ValueError:
        return wireproto.pusherr(_('Invalid payload.'))

    assert version == 1
    lines = data.split('\n')[1:]

    o = {
        'bzusername': None,
        'bzpassword': None,
        'bzcookie': None,
        'bzuserid': None,
        'other': []
    }

    for line in lines:
        t, d = line.split(' ', 1)

        if t == 'bzusername':
            o['bzusername'] = urllib.unquote(d)
        elif t == 'bzpassword':
            o['bzpassword'] = urllib.unquote(d)
        elif t == 'bzuserid':
            o['bzuserid'] = urllib.unquote(d)
        elif t == 'bzcookie':
            o['bzcookie'] = urllib.unquote(d)
        else:
            o['other'].append((t, d))

    return o

def getrbapi(repo, o):
    from rbtools.api.client import RBClient

    url = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    c = RBClient(url, username=o['bzusername'], password=o['bzpassword'])
    return c.get_root()

@wireproto.wireprotocommand('pushreview', '*')
def reviewboard(repo, proto, args=None):
    proto.redirect()

    o = parsepayload(proto, args)
    if isinstance(o, wireproto.pusherr):
        return o

    bzusername = o['bzusername']
    bzpassword = o['bzpassword']
    bzuserid = o['bzuserid']
    bzcookie = o['bzcookie']
    identifier = None
    nodes = []

    for t, d in o['other']:
        if t == 'reviewidentifier':
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

    parentrid, commitmap, reviews = post_reviews(rburl, repoid, identifier,
                                                 commits,
                                                 username=bzusername,
                                                 password=bzpassword,
                                                 cookie=bzcookie)

    lines = [
        '1',
        'rburl %s' % rburl,
        'reviewid %s' % identifier,
        'parentreview %s' % parentrid,
        'reviewdata %s status %s' % (parentrid,
            urllib.quote(reviews[parentrid].status.encode('utf-8'))),
    ]

    for node, rid in commitmap.items():
        rr = reviews[rid]
        lines.append('csetreview %s %s' % (node, rid))
        lines.append('reviewdata %s status %s' % (rid,
            urllib.quote(rr.status.encode('utf-8'))))

    # It's easy for unicode to creep in from RBClient APIs. Mercurial doesn't
    # like unicode type responses, so catch it early and avoid the crypic
    # KeyError: <type 'unicode'> in Mercurial.
    res = '\n'.join(lines)
    assert isinstance(res, str)
    return res

@wireproto.wireprotocommand('pullreviews', '*')
def pullreviews(repo, proto, args=None):
    proto.redirect()

    o = parsepayload(proto, args)
    if isinstance(o, wireproto.pusherr):
        return o

    root = getrbapi(repo, o)

    lines = ['1']

    for k, v in o['other']:
        if k != 'rid':
            continue

        rr = root.get_review_request(review_request_id=v)

        lines.append('reviewdata %s status %s' % (v,
            urllib.quote(rr.status.encode('utf-8'))))

    res = '\n'.join(lines)
    assert isinstance(res, str)

    return res
