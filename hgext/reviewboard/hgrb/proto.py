# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import json
import os
from StringIO import StringIO
import xmlrpclib

from mercurial.node import short
from mercurial import (
    demandimport,
    encoding,
    error,
    mdiff,
    patch,
    phases,
    util,
    wireproto,
)

from mozautomation import commitparser
from hgrb.util import ReviewID


API_KEY_NEEDED = (
    'Bugzilla API keys are now used by MozReview; '
    'see https://mozilla-version-control-tools.readthedocs.io/en/latest/mozreview/install.html#obtaining-accounts-credentials-and-privileges '
    'for instructions on how to configure your client')


class AuthorizationError(Exception):
    """Represents an error authenticating or authorizing to Bugzilla."""

    def __init__(self, e, username=None, apikey=None, **kwargs):
        self.e = e
        self.username = username
        self.apikey = apikey

        self.web_login_needed = e.rsp.get('web_login_needed', False)
        self.login_url = e.rsp.get('login_url', None)
        self.bugzilla_api_key_needed = e.rsp.get('bugzilla_api_key_needed', False)
        self.bugzilla_api_key_url = e.rsp.get('bugzilla_api_key_url', False)

    def __str__(self):
        if self.bugzilla_api_key_needed:
            return API_KEY_NEEDED

        if self.web_login_needed:
            return 'Web login needed; log in at %s then try again' % self.login_url

        if self.apikey:
            return("%s\nLog out and back in to Review Board then try again"
                   % self.e.args[0])
        else:
            return 'unknown failure'


class BadRequestError(Exception):
    """Represents an error making a request to Reviewboard."""

    def __init__(self, e):
        self.e = e

    def __str__(self):
        return self.e.args[0]


class ServerError(Exception):
    """Represents an error that occurred during processing."""
    def __init__(self, s):
        assert isinstance(s, str)
        self.s = s

    def __str__(self):
        return 'error %s' % self.s


class NoAPITokenAuthError(ServerError):
    """Error when client sends deprecated authentication credential types."""
    def __init__(self):
        super(NoAPITokenAuthError, self).__init__('irrelevant')

    def __str__(self):
        return 'error %s' % API_KEY_NEEDED


# Wrap reviewboardmods and error types because we don't want to require the
# clients to import rbtools.
def post_reviews(*args, **kwargs):
    from rbtools.api import errors

    try:
        return submit_reviews(*args, **kwargs)
    except errors.AuthorizationError as e:
        raise AuthorizationError(e, **kwargs)
    except errors.BadRequestError as e:
        raise BadRequestError(e)
    except errors.APIError as e:
        raise BadRequestError(e)


def submit_reviews(url, repoid, identifier, commits, privileged_username,
                   privileged_password, username=None, apikey=None):
    """Submit commits to Review Board."""
    # Workaround an issue with "import _imp" in pkg_resources.
    with demandimport.deactivated():
        from reviewboardmods.pushhooks import ReviewBoardClient

    client = ReviewBoardClient(url, username=privileged_username,
                               password=privileged_password)
    root = client.get_root()

    batch_request_resource = root.get_extension(
        extension_name='mozreview.extension.MozReviewExtension')\
        .get_batch_review_requests()
    series_result = batch_request_resource.create(
        username=username,
        api_key=apikey,
        # This assumes that we pushed to the repository/URL that Review Board is
        # configured to use. This assumption may not always hold.
        repo_id=repoid,
        identifier=identifier,
        commits=json.dumps(commits, encoding='utf-8'))

    nodes = {node.encode('utf-8'): str(rid)
             for node, rid in series_result.nodes.iteritems()}

    return (
        str(series_result.squashed_rr),
        nodes,
        series_result.review_requests,
        series_result.warnings,
    )


def associate_ldap_username(*args, **kwargs):
    # Workaround an issue with "import _imp" in pkg_resources.
    with demandimport.deactivated():
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


def parsejsonpayload(proto, args):
    return json.loads(getpayload(proto, args), encoding='utf-8')


def errorresponse(msg):
    return {'error': msg}


@wireproto.wireprotocommand('pushreview', '*')
def pushreviewwireprotocommand(repo, proto, args=None):
    proto.redirect()
    req = parsejsonpayload(proto, args)

    # We support pushing via HTTP and SSH. REMOTE_USER will be set via HTTP.
    # USER via SSH. But USER is a common variable and could also sneak into
    # the HTTP environment.
    #
    # REMOTE_USER values come from Bugzilla. USER values come from LDAP.
    # There is a potential privilege escalation vulnerability if someone
    # obtains a Bugzilla account overlapping with a LDAP user having
    # special privileges. So, we explicitly don't perform an LDAP lookup
    # if REMOTE_USER is present because we could be crossing the user
    # stores.
    ldap_username = os.environ.get('USER')
    remote_user = repo.ui.environ.get('REMOTE_USER', os.environ.get('REMOTE_USER'))
    if remote_user:
        ldap_username = None

    res = _processpushreview(repo, req, ldap_username)
    return json.dumps(res, sort_keys=True)


if util.safehasattr(wireproto, 'permissions'):
    wireproto.permissions['pushreview'] = 'push'


def _processpushreview(repo, req, ldap_username):
    """Handle a request to turn changesets into review requests.

    ``ldap_username`` is the LDAP username to associate with the MozReview
    account whose credentials are passed as part of the request. We implicitly
    trust the passed LDAP username has been authenticated to belong to the
    MozReview account.
    """
    bzusername = req.get('bzusername')
    bzapikey = req.get('bzapikey')

    if not bzusername or not bzapikey:
        return errorresponse('Bugzilla API keys not configured; see '
            'https://mozilla-version-control-tools.readthedocs.io/en/latest/mozreview/install.html#obtaining-accounts-credentials-and-privileges '
            'for instructions on how to configure your client')

    identifier = req['identifier']
    nodes = []
    precursors = {}
    for cset in req['changesets']:
        node = cset['node']
        nodes.append(node)
        if 'precursors' in cset:
            precursors[node] = cset['precursors']

    diffopts = mdiff.diffopts(context=8, showfunc=True, git=True)

    commits = {
        'individual': [],
        'squashed': {},
        'obsolescence': req.get('obsolescence', False),
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
            return errorresponse(msg)

    # Invalid or confidental bugs will raise errors in the Review Board
    # interface later. Fail fast to minimize wasted time and resources.
    try:
        reviewid = ReviewID(identifier)
    except error.Abort as e:
        return errorresponse(str(e))

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
            return errorresponse('bug %s does not exist; '
                'please change the review id (%s)' % (reviewid.bug,
                    reviewid.full))
        elif f.faultCode == 102:
            return errorresponse('bug %s could not be accessed '
                '(we do not currently allow posting of reviews to '
                'confidential bugs)' % reviewid.bug)

        return errorresponse('server error verifying bug %s exists; '
            'please retry or report a bug' % reviewid.bug)

    # Find the first public node in the ancestry of this series. This is
    # used by MozReview to query the upstream repo for additional context.
    first_public_ancestor = None
    for node in repo[nodes[0]].ancestors():
        ctx = repo[node]
        if ctx.phase() == phases.public:
            first_public_ancestor = ctx.hex()
            break
    commits['squashed']['first_public_ancestor'] = first_public_ancestor

    # Note patch.diff() appears to accept anything that can be fed into
    # repo[]. However, it blindly does a hex() on the argument as opposed
    # to the changectx, so we need to pass in the binary node.
    base_ctx = repo[nodes[0]].p1()
    base_parent_node = base_ctx.node()
    for i, node in enumerate(nodes):
        ctx = repo[node]
        p1 = ctx.p1().node()

        diff = ''.join(patch.diff(repo, node1=p1, node2=ctx.node(), opts=diffopts)) + '\n'

        if i:
            base_commit_id = nodes[i-1]
        else:
            base_commit_id = base_ctx.hex()

        summary = encoding.fromlocal(ctx.description().splitlines()[0])
        if req.get('deduce-reviewers', True):
            reviewers = list(commitparser.parse_rquestion_reviewers(summary))
            requal_reviewers = list(commitparser.parse_requal_reviewers(summary))
        else:
            reviewers = []
            requal_reviewers = []
        commits['individual'].append({
            'id': node,
            'author': encoding.fromlocal(ctx.user()),
            'precursors': precursors.get(node, []),
            'message': encoding.fromlocal(ctx.description()),
            # Diffs are arbitrary byte sequences. json.dump() will try to
            # interpret str as UTF-8, which could fail. Instead of trying
            # to coerce the str to a unicode or use ensure_ascii=False (which
            # is a giant pain), just base64 encode the diff in the JSON.
            'diff_b64': diff.encode('base64'),
            'bug': str(reviewid.bug),
            'base_commit_id': base_commit_id,
            'first_public_ancestor': first_public_ancestor,
            'reviewers': reviewers,
            'requal_reviewers': requal_reviewers
        })

    squashed_diff = b''.join(patch.diff(repo,
                                        node1=base_parent_node,
                                        node2=repo[nodes[-1]].node(),
                                        opts=diffopts)) + '\n'

    commits['squashed']['diff_b64'] = squashed_diff.encode('base64')
    commits['squashed']['base_commit_id'] = base_ctx.hex()

    rburl = repo.ui.config('reviewboard', 'url', None).rstrip('/')
    repoid = repo.ui.configint('reviewboard', 'repoid', None)
    privileged_rb_username = repo.ui.config('reviewboard', 'username', None)
    privileged_rb_password = repo.ui.config('reviewboard', 'password', None)

    if ldap_username:
        associate_ldap_username(rburl, ldap_username, privileged_rb_username,
                                privileged_rb_password, username=bzusername,
                                apikey=bzapikey)

    res = {
        'rburl': rburl,
        'reviewid': identifier,
        'reviewrequests': {},
        'display': [],
    }

    try:
        parentrid, commitmap, reviews, warnings = \
            post_reviews(rburl, repoid, identifier, commits,
                         privileged_rb_username, privileged_rb_password,
                         username=bzusername, apikey=bzapikey)

        res['display'].extend(warnings)
        res['parentrrid'] = parentrid
        res['reviewrequests'][parentrid] = {
            'status': reviews[parentrid]['status'],
            'public': reviews[parentrid]['public'],
        }

        for node, rid in commitmap.items():
            rd = reviews[rid]
            res['reviewrequests'][rid] = {
                'node': node,
                'status': rd['status'],
                'public': rd['public'],
            }

            if rd['reviewers']:
                res['reviewrequests'][rid]['reviewers'] = list(rd['reviewers'])

    except AuthorizationError as e:
        return errorresponse(str(e))
    except BadRequestError as e:
        return errorresponse(str(e))

    return res


@wireproto.wireprotocommand('pullreviews', '*')
def pullreviews(repo, proto, args=None):
    proto.redirect()
    req = parsejsonpayload(proto, args)

    # Workaround an issue with "import _imp" in pkg_resources.
    with demandimport.deactivated():
        from reviewboardmods.pushhooks import ReviewBoardClient
    client = ReviewBoardClient(repo.ui.config('reviewboard', 'url').rstrip('/'),
                               username=req.get('bzusername'),
                               apikey=req.get('bzapikey'))
    root = client.get_root()

    res = {
        'reviewrequests': {},
    }

    for identifier in req.get('identifiers', []):
        rrs = root.get_review_requests(commit_id=identifier)

        if rrs.total_results != 1:
            continue

        rr = rrs[0]
        commit_data = client.get_path(
            '/extensions/mozreview.extension.MozReviewExtension/'
            'commit-data/%s/' % rr.id)

        try:
            is_squashed = commit_data.extra_data['p2rb.is_squashed']
        except KeyError:
            is_squashed = None

        # 'True' in RB <= 2.0.11; True in 2.0.11+. We may have old
        # values in the database, so keep checking for 'True' until we
        # have a migration.
        if is_squashed is True or is_squashed == 'True':
            if 'p2rb.commits' in commit_data.extra_data:
                commits = commit_data.extra_data['p2rb.commits']
            else:
                draft = rr.get_draft()
                if 'p2rb.commits' in commit_data.draft_extra_data:
                    commits = commit_data.draft_extra_data['p2rb.commits']
                else:
                    commits = '[]'

            for relation in json.loads(commits):
                rid = str(relation[1])

                res['reviewrequests'][str(rid)] = {
                    'status': rr.status,
                    'public': rr.public,
                }

        res['reviewrequests'][str(rr.id)] = {
            'status': rr.status,
            'public': rr.public,
            'reviewers': [p.title for p in rr.target_people],
        }

    return json.dumps(res, sort_keys=True)


if util.safehasattr(wireproto, 'permissions'):
    wireproto.permissions['pullreviews'] = 'pull'


@wireproto.wireprotocommand('publishreviewrequests', '*')
def publishreviewseries(repo, proto, args=None):
    """Publish review requests.

    Payload consists of line-delimited metadata, just like other commands.
    Entries for "reviewid %d" correspond to review requests that will be
    published as part of the request.

    Note: MozReview will publish all children when publishing a parent review
    request.
    """
    proto.redirect()
    req = parsejsonpayload(proto, args)
    res = _processpublishreview(repo, req)
    return json.dumps(res, sort_keys=True)


if util.safehasattr(wireproto, 'permissions'):
    wireproto.permissions['publishreviewrequests'] = 'push'


def _processpublishreview(repo, req):
    from rbtools.api.errors import APIError
    # Workaround an issue with "import _imp" in pkg_resources.
    with demandimport.deactivated():
        from reviewboardmods.pushhooks import ReviewBoardClient
    client = ReviewBoardClient(repo.ui.config('reviewboard', 'url').rstrip('/'),
                               username=req['bzusername'],
                               apikey=req['bzapikey'])
    root = client.get_root()

    res = {
        'results': [],
    }

    for rrid in req.get('rrids', []):
        try:
            rr = root.get_review_request(review_request_id=rrid)
            draft = rr.get_draft()
            draft.update(public=True)
            res['results'].append({'rrid': rrid, 'success': True})
        except APIError as e:
            res['results'].append({'rrid': rrid, 'error': unicode(e)})

    return res


@wireproto.wireprotocommand('listreviewrepos')
def listreviewrepos(repo, proto, args=None):
    """List review repositories we can push to.

    Should only be called by clients pushing to a repo that doesn't support
    pushing reviews. Returns empty string if nothing is defined, which is
    harmless.
    """
    # TODO convert on disk format to JSON
    d = {}
    for line in repo.vfs.tryreadlines('reviewrepos'):
        line = line.strip()
        node, urls = line.split(' ', 1)
        urls = urls.split(' ')
        d[node] = urls
    return json.dumps(d, sort_keys=True)


if util.safehasattr(wireproto, 'permissions'):
    wireproto.permissions['listreviewrepos'] = 'pull'
