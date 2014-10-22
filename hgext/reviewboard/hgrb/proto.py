# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import json
import urllib
from StringIO import StringIO
from mercurial import mdiff
from mercurial import patch
from mercurial import wireproto
from mercurial.node import short

class AuthError(Exception):
    """Represents an error authenticating or authorizing to Bugzilla."""

    def __init__(self, e, username, password, userid, cookie, **kwargs):
        self.e = e
        self.username = username
        self.password = password
        self.userid = userid
        self.cookie = cookie

    def __str__(self):
        if self.password:
            return 'invalid Bugzilla username/password; check your settings'
        if self.cookie:
            return 'invalid Bugzilla login cookie; is it expired?'
        else:
            return 'unknown failure'

# Wrap post_reviews because we don't want to require the clients to
# import rbtools.
def post_reviews(*args, **kwargs):
    from reviewboardmods.pushhooks import post_reviews as pr
    from rbtools.api.errors import AuthorizationError

    try:
        return pr(*args, **kwargs)
    except AuthorizationError as e:
        # Reraise as our internal type to avoid import issues.
        raise AuthError(e, **kwargs)

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
    precursors = {}

    for t, d in o['other']:
        if t == 'reviewidentifier':
            identifier = urllib.unquote(d)
        elif t == 'csetreview':
            # This detects old versions of the client from before official
            # release.
            fields = d.split(' ')
            if len(fields) != 1:
                return wireproto.pusherr(_('old reviewboard client detected; please upgrade'))
            nodes.append(d)
        elif t == 'precursors':
            node, before = d.split(' ', 1)
            precursors[node] = before.split()

    if not identifier:
        return wireproto.pusherr(_('no review identifier in request'))

    diffopts = mdiff.diffopts(context=8, showfunc=True)

    commits = {
        'individual': [],
        'squashed': {}
    }

    def formatresponse(*lines):
        l = ['1'] + list(lines)
        res = '\n'.join(l)
        # It's easy for unicode to creep in from RBClient APIs. Mercurial
        # doesn't like unicode type responses, so catch it early and avoid
        # the crypic KeyError: <type 'unicode'> in Mercurial.
        assert isinstance(res, str)
        return res

    # Note patch.diff() is appears to accept anything that can be fed into
    # repo[]. However, it blindly does a hex() on the argument as opposed
    # to the changectx, so we need to pass in the binary node.
    base_parent_node = repo[nodes[0]].p1().node()
    for i, node in enumerate(nodes):
        ctx = repo[node]

        # Reviewing merge commits doesn't make much sense and only makes
        # situations more complicated. So disallow the practice.
        if len(ctx.parents()) > 1:
            msg = 'cannot review merge commits (%s)' % short(ctx.node())
            return formatresponse('error %s' % msg)

        p1 = ctx.p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=ctx.node(), opts=diffopts))
        if i:
            parent_diff = ''.join(patch.diff(repo, node1=base_parent_node,
                node2=repo[nodes[i-1]].node(), opts=diffopts))

        commits['individual'].append({
            'id': node,
            'precursors': precursors.get(node, []),
            'message': ctx.description(),
            'diff': diff,
            'parent_diff': parent_diff,
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=base_parent_node,
        node2=repo[nodes[-1]].node(), opts=diffopts))

    rburl = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    repoid = repo.ui.configint('reviewboard', 'repoid', None)

    lines = [
        'rburl %s' % rburl,
        'reviewid %s' % identifier,
    ]

    try:
        parentrid, commitmap, reviews = post_reviews(rburl, repoid, identifier,
                                                     commits,
                                                     username=bzusername,
                                                     password=bzpassword,
                                                     userid=bzuserid,
                                                     cookie=bzcookie)
        lines.extend([
            'parentreview %s' % parentrid,
            'reviewdata %s status %s' % (parentrid,
                urllib.quote(reviews[parentrid].status.encode('utf-8'))),
        ])

        for node, rid in commitmap.items():
            rr = reviews[rid]
            lines.append('csetreview %s %s' % (node, rid))
            lines.append('reviewdata %s status %s' % (rid,
                urllib.quote(rr.status.encode('utf-8'))))

    except AuthError as e:
        lines.append('error %s' % str(e))

    res = formatresponse(*lines)
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
        if k != 'reviewid':
            continue

        identifier = urllib.unquote(v)
        rrs = root.get_review_requests(commit_id=identifier)

        if rrs.total_results != 1:
            continue

        rr = rrs[0]
        extra_data = rr.extra_data

        if 'p2rb.is_squashed' in extra_data and extra_data['p2rb.is_squashed'] == 'True':
            if 'p2rb.commits' in extra_data:
                commits = extra_data['p2rb.commits']
            else:
                draft = rr.get_draft()
                if 'p2rb.commits' in draft.extra_data:
                    commits = draft.extra_data['p2rb.commits']
                else:
                    commits = '[]'

            lines.append('parentreview %s %s' % (
                urllib.quote(identifier), rr.id))
            for relation in json.loads(commits):
                node = relation[0].encode('utf-8')
                rid = relation[1].encode('utf-8')

                lines.append('csetreview %s %s %s' % (rr.id, node, rid))
                lines.append('reviewdata %s status %s' % (rid,
                    urllib.quote(rr.status.encode('utf-8'))))

        lines.append('reviewdata %s status %s' % (rr.id,
            urllib.quote(rr.status.encode('utf-8'))))

    res = '\n'.join(lines)
    assert isinstance(res, str)

    return res
