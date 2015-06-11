# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os
import urllib
from StringIO import StringIO
import xmlrpclib
from mercurial import mdiff
from mercurial import patch
from mercurial import wireproto
from mercurial.node import short

from hgrb.util import ReviewID

from mozautomation import commitparser


class AuthorizationError(Exception):
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


class BadRequestError(Exception):
    """Represents an error making a request to Reviewboard."""

    def __init__(self, e):
        self.e = e

    def __str__(self):
        return ('reviewboard error: "%s". please try submitting the'
                ' review again. if that doesn\'t work, you\'ve likely'
                ' encountered a bug.') % str(self.e).splitlines()[0]


# Wrap reviewboardmods and error types because we don't want to require the
# clients to import rbtools.
def post_reviews(*args, **kwargs):
    from reviewboardmods.pushhooks import post_reviews as pr
    from rbtools.api import errors

    try:
        return pr(*args, **kwargs)
    except errors.AuthorizationError as e:
        raise AuthorizationError(e, **kwargs)
    except errors.BadRequestError as e:
        raise BadRequestError(e)

def associate_ldap_username(*args, **kwargs):
    from reviewboardmods.pushhooks import associate_ldap_username as alu
    return alu(*args, **kwargs)


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


def parseidentifier(o):
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
                identifier = wireproto.pusherr(_('old reviewboard client detected; please upgrade'))
            nodes.append(d)
        elif t == 'precursors':
            node, before = d.split(' ', 1)
            precursors[node] = before.split()

    return identifier, nodes, precursors


def getrbapi(repo, o):
    from rbtools.api.client import RBClient

    url = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    c = RBClient(url, username=o['bzusername'], password=o['bzpassword'])
    return c.get_root()


def formatresponse(*lines):
    l = ['1'] + list(lines)
    res = '\n'.join(l)
    # It's easy for unicode to creep in from RBClient APIs. Mercurial
    # doesn't like unicode type responses, so catch it early and avoid
    # the crypic KeyError: <type 'unicode'> in Mercurial.
    assert isinstance(res, str)
    return res


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

    identifier, nodes, precursors = parseidentifier(o)
    if not identifier:
        return wireproto.pusherr(_('no review identifier in request'))

    diffopts = mdiff.diffopts(context=8, showfunc=True, git=True)

    commits = {
        'individual': [],
        'squashed': {}
    }

    # We do multiple passes over the changesets requested for review because
    # some operations could be slow or may involve queries to external
    # resources. We want to run the fast checks first so we don't waste
    # resources before finding the error. The drawback here is the client
    # will not see the full set of errors. We may revisit this decision
    # later.

    for node in nodes:
        ctx = repo[node]
        # Reviewing merge commits doesn't make much sense and only makes
        # situations more complicated. So disallow the practice.
        if len(ctx.parents()) > 1:
            msg = 'cannot review merge commits (%s)' % short(ctx.node())
            return formatresponse('error %s' % msg)

    # Invalid or confidental bugs will raise errors in the Review Board
    # interface later. Fail fast to minimize wasted time and resources.
    try:
        reviewid = ReviewID(identifier)
    except util.Abort as e:
        return formatresponse('error %s' % e)

    if reviewid.bug:
        # We use xmlrpc here because the Bugsy REST client doesn't currently handle
        # errors in responses.

        # We don't use available Bugzilla credentials because that's the
        # easiest way to test for confidential bugs. If/when we support posting
        # reviews to confidential bugs, we'll need to change this.
        xmlrpc_url = repo.ui.config('bugzilla', 'url').rstrip('/') + '/xmlrpc.cgi'
        proxy = xmlrpclib.ServerProxy(xmlrpc_url)
        try:
            proxy.Bug.get({'ids': [reviewid.bug]})
        except xmlrpclib.Fault as f:
            if f.faultCode == 101:
                return formatresponse('error bug %s does not exist; '
                    'please change the review id (%s)' % (reviewid.bug,
                        reviewid.full))
            elif f.faultCode == 102:
                return formatresponse('error bug %s could not be accessed '
                    '(we do not currently allow posting of reviews to '
                    'confidential bugs)' % reviewid.bug)

            return formatresponse('error server error verifying bug %s exists; '
                'please retry or report a bug' % reviewid.bug)

    # Note patch.diff() appears to accept anything that can be fed into
    # repo[]. However, it blindly does a hex() on the argument as opposed
    # to the changectx, so we need to pass in the binary node.
    base_ctx = repo[nodes[0]].p1()
    base_parent_node = base_ctx.node()
    for i, node in enumerate(nodes):
        ctx = repo[node]
        p1 = ctx.p1().node()
        diff = None
        parent_diff = None

        diff = ''.join(patch.diff(repo, node1=p1, node2=ctx.node(), opts=diffopts)) + '\n'

        if i:
            base_commit_id = nodes[i-1]
        else:
            base_commit_id = base_ctx.hex()
        summary = ctx.description().splitlines()[0]
        commits['individual'].append({
            'id': node,
            'precursors': precursors.get(node, []),
            'message': ctx.description(),
            'diff': diff,
            'base_commit_id': base_commit_id,
            'reviewers': list(commitparser.parse_reviewers(summary))
        })

    commits['squashed']['diff'] = ''.join(patch.diff(repo, node1=base_parent_node,
        node2=repo[nodes[-1]].node(), opts=diffopts)) + '\n'
    commits['squashed']['base_commit_id'] = base_ctx.hex()

    rburl = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    repoid = repo.ui.configint('reviewboard', 'repoid', None)
    privleged_rb_username = repo.ui.config('reviewboard', 'username', None)
    privleged_rb_password = repo.ui.config('reviewboard', 'password', None)

    ldap_username = os.environ.get('USER')

    if ldap_username:
        associate_ldap_username(rburl, ldap_username, privleged_rb_username,
                                privleged_rb_password, username=bzusername,
                                password=bzpassword, userid=bzuserid,
                                cookie=bzcookie)

    lines = [
        'rburl %s' % rburl,
        'reviewid %s' % identifier,
    ]

    try:
        parentrid, commitmap, reviews = post_reviews(rburl, repoid, identifier,
                                                     commits, lines,
                                                     username=bzusername,
                                                     password=bzpassword,
                                                     userid=bzuserid,
                                                     cookie=bzcookie)
        lines.extend([
            'parentreview %s' % parentrid,
            'reviewdata %s status %s' % (parentrid,
                urllib.quote(reviews[parentrid].status.encode('utf-8'))),
            'reviewdata %s public %s' % (parentrid, reviews[parentrid].public),
        ])

        for node, rid in commitmap.items():
            rr = reviews[rid]
            lines.append('csetreview %s %s' % (node, rid))
            lines.append('reviewdata %s status %s' % (rid,
                urllib.quote(rr.status.encode('utf-8'))))
            lines.append('reviewdata %s public %s' % (rid, rr.public))

    except AuthorizationError as e:
        lines.append('error %s' % str(e))
    except BadRequestError as e:
        lines.append('error %s' % str(e))

    res = formatresponse(*lines)
    return res

@wireproto.wireprotocommand('pullreviews', '*')
def pullreviews(repo, proto, args=None):
    import json

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

        try:
            is_squashed = extra_data['p2rb.is_squashed']
        except KeyError:
            is_squashed = None

        # 'True' in RB <= 2.0.11; True in 2.0.11+. We may have old
        # values in the database, so keep checking for 'True' until we
        # have a migration.
        if is_squashed is True or is_squashed == 'True':
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
                rid = str(relation[1])

                lines.append('csetreview %s %s %s' % (rr.id, node, rid))
                lines.append('reviewdata %s status %s' % (rid,
                    urllib.quote(rr.status.encode('utf-8'))))
                lines.append('reviewdata %s public %s' % (rid, rr.public))

        lines.append('reviewdata %s status %s' % (rr.id,
            urllib.quote(rr.status.encode('utf-8'))))
        lines.append('reviewdata %s public %s' % (rr.id, rr.public))

    res = '\n'.join(lines)
    assert isinstance(res, str)

    return res
