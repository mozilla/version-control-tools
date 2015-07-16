# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board client extension.

This extensions enables clients to easily create Review Board reviews
when pushing to a remote server.

When a client with this extension installed pushes to a remote that has the
corresponding server extension installed, the client will create a Review
Board review automatically.

This extension adds new options to the `push` command:

  * --noreview If present, we will not attempt to perform a review
    automatically when pushing. This is typically only useful for
    testing or ensuring certain commits are present on the remote.
  * --reviewid The review identifier to use. Pushes using the same
    review ID will overwrite existing reviews for that ID.
  * -c Single changeset to review.
"""

import errno
import os
import sys
import urllib

from mercurial import (
    cmdutil,
    commands,
    context,
    demandimport,
    exchange,
    extensions,
    hg,
    httppeer,
    localrepo,
    obsolete,
    phases,
    scmutil,
    sshpeer,
    templatekw,
    util,
)
from mercurial.i18n import _
from mercurial.node import bin, hex

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

demandimport.disable()
try:
    import hgrb.proto
except ImportError:
    sys.path.insert(0, OUR_DIR)

    import hgrb.proto
demandimport.enable()

from hgrb.util import (
    genid,
    ReviewID,
)

from mozautomation.commitparser import parse_bugs, parse_requal_reviewers
from mozhg.auth import getbugzillaauth
from mozhg.rewrite import (
    newparents,
    replacechangesets,
)

testedwith = '3.1 3.2 3.3 3.4'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=MozReview'

cmdtable = {}
command = cmdutil.command(cmdtable)


clientcapabilities = {
    'proto1',
    'listreviewdata',
}

def decodepossiblelistvalue(v):
    """Decode a wire protocol value that may be a list.

    Values are URL encoded. Lists have literal "," separating elements.
    """
    if ',' in v:
        return [urllib.unquote(p) for p in v.split(',')]
    else:
        return urllib.unquote(v)

PROTOVERSION = 1


def commonrequestlines(ui, bzauth=None):
    """Obtain a list of lines common in protocol requests."""
    lines = ['%d' % PROTOVERSION]

    # Tell the server we support examining capabilities.
    #
    # This is behind a config flag to facilitate testing.
    if ui.configbool('reviewboard', 'supportscaps', True):
        lines.append('supportscaps 1')

    for p in ('username', 'password', 'userid', 'cookie'):
        if getattr(bzauth, p, None):
            lines.append('bz%s %s' % (p, urllib.quote(getattr(bzauth, p))))

    return lines

def getpayload(s):
    """Obtain the payload of a response from the server.

    All responses begin with the protocol version followed by a newline.
    Currently, we only support version 1.

    Returns a list of lines in the response.
    """
    try:
        off = s.index('\n')
        version = int(s[0:off])

        if version != PROTOVERSION:
            raise util.Abort(_('unrecognized protocol version from server'))
    except ValueError:
        raise util.Abort(_('invalid response from server'))

    assert version == PROTOVERSION
    lines = s.split('\n')[1:]
    return lines

def getreviewcaps(remote):
    """Obtain a set of review capabilities from the server.

    Returns empty set if no capabilities are defined (and the server presumably
    isn't a review repo).

    As a side effect, this function also validates that the client fulfills the
    advertised minimum requirements set by the server and aborts if not.
    """
    requires = remote.capable('mozreviewrequires')
    if isinstance(requires, str):
        requires = set(requires.split(','))
        if requires - clientcapabilities:
            raise util.Abort(
                _('reviewboard client extension is too old to speak to this '
                  'server'),
                hint=_('upgrade your extension by running `hg -R %s pull -u`') %
                       os.path.normpath(os.path.join(OUR_DIR, '..', '..')))

    caps = remote.capable('mozreview')
    if isinstance(caps, bool):
        caps = ''

    return set(caps.split(','))


def pushcommand(orig, ui, repo, *args, **kwargs):
    """Wraps commands.push to read the --reviewid argument."""

    ReviewID(kwargs['reviewid'])

    if kwargs['rev'] and kwargs['changeset']:
        raise util.Abort(_('cannot specify both -r and -c'))

    # There isn't a good way to send custom arguments to the push api. So, we
    # inject some temporary values on the repo. This may fail in many
    # scenarios, most of them related to server operation.
    repo.noreviewboardpush = kwargs['noreview']
    repo.reviewid = kwargs['reviewid']

    # -c implies -r <rev> with an identical base node.
    if kwargs['changeset']:
        kwargs['rev'] = [kwargs['changeset']]
        repo.pushsingle = True
    else:
        repo.pushsingle = False

    try:
        return orig(ui, repo, *args, **kwargs)
    finally:
        repo.noreviewboardpush = None
        repo.reviewid = None
        repo.pushsingle = None

# kwargs is here for "bookmarks," which was introduced in Mercurial 3.2. We
# can add it explicitly once support for <3.2 has been dropped.
def wrappedpush(orig, repo, remote, force=False, revs=None, newbranch=False,
                **kwargs):
    """Wraps exchange.push to enforce restrictions for review pushes."""

    # The repository does not support pushing reviews.
    caps = getreviewcaps(remote)
    if 'pushreview' not in caps:
        # See if this repository is a special "discovery" repository
        # and follow the link, if present.
        if 'listreviewrepos' not in caps:
            return orig(repo, remote, force=force, revs=revs,
                        newbranch=newbranch, **kwargs)

        repo.ui.status(_('searching for appropriate review repository\n'))
        repos = remote.listkeys('reviewrepos')
        rootnode = repo[0].hex()
        newurl = None
        for url, node in repos.items():
            if rootnode == node:
                newurl = url
                break
        else:
            raise util.Abort(_('no review repository found'))

        newurl = util.url(newurl)
        oldurl = util.url(remote._url)

        # We don't currently allow redirecting to different protocols
        # or hosts. This is due to abundance of caution around
        # security concerns.

        if newurl.scheme != oldurl.scheme or newurl.host != oldurl.host:
            raise util.Abort(_('refusing to redirect due to URL mismatch: %s' %
                newurl))

        repo.ui.status(_('redirecting push to %s\n') % newurl)

        if isinstance(remote, httppeer.httppeer):
            remote._url = str(newurl)

            newurl.user = oldurl.user
            newurl.passwd = oldurl.passwd
            remote.path = str(newurl)
            newremote = remote

        elif isinstance(remote, sshpeer.sshpeer):
            newurl.user = oldurl.user

            # SSH remotes establish processes. We can't simply monkeypatch
            # the instance.
            newremote = type(remote)(remote.ui, str(newurl))
        else:
            raise util.Abort(_('do not know how to talk to this remote type\n'))

        return wrappedpush(orig, repo, newremote, force=False, revs=revs,
                           newbranch=False, **kwargs)

    ircnick = repo.ui.config('mozilla', 'ircnick', None)
    if not ircnick:
        raise util.Abort(_('you must set mozilla.ircnick in your hgrc config '
            'file to your IRC nickname in order to perform code reviews'))

    # We filter the "extension isn't installed" message from the server.
    # This is a bit hacky, but it's easier than sending a signal over the
    # wire protocol (at least until bundle2).

    def filterwrite(messages):
        # Mercurial 3.5 sends the output as one string.
        if messages[0].startswith('%sREVIEWBOARD' % _('remote: ')):
            return True

        # Older versions have separate components.
        if messages[0] == _('remote: ') and len(messages) >= 2 and \
            messages[1].startswith('REVIEWBOARD: '):
            return True

        return False

    # Starting with Mercurial 3.5 or possibly bundle2, remote messages are
    # now written to the repo's ui instance as opposed to the remote's. We
    # wrap both instances until we drop support for Mercurial 3.4.
    oldrepocls = repo.ui.__class__
    oldremotecls = remote.ui.__class__

    class repofilteringwrite(repo.ui.__class__):
        def write(self, *args, **kwargs):
            if not filterwrite(args):
                return oldrepocls.write(self, *args, **kwargs)

    class remotefilteringwrite(remote.ui.__class__):
        def write(self, *args, **kwargs):
            if not filterwrite(args):
                return oldremotecls.write(self, *args, **kwargs)

    repo.ui.__class__ = repofilteringwrite
    remote.ui.__class__ = remotefilteringwrite
    try:
        # We always do force push because we don't want users to need to
        # specify it. The big danger here is pushing multiple heads or
        # branches or mq patches. We check the former above and we don't
        # want to limit user choice on the latter two.
        return orig(repo, remote, force=True, revs=revs, newbranch=newbranch,
                **kwargs)
    finally:
        repo.ui.__class__ = oldrepocls
        remote.ui.__class__ = oldremotecls


def wrappedpushdiscovery(orig, pushop):
    """Wraps exchange._pushdiscovery to add extra review metadata.

    We discover what nodes to review before discovery. This ensures that
    errors are discovered and reported quickly, without waiting for
    server communication.
    """

    pushop.reviewnodes = None

    caps = getreviewcaps(pushop.remote)
    if 'pushreview' not in caps:
        return orig(pushop)

    ui = pushop.ui
    repo = pushop.repo

    if repo.noreviewboardpush:
        return orig(pushop)

    # If no arguments are specified to push, Mercurial will try to push all
    # non-remote changesets by default. This can result in unexpected behavior,
    # especially for people doing multi-headed development.
    #
    # Since we reject pushes with multiple heads anyway, default to pushing
    # the working copy.
    if not pushop.revs:
        pushop.revs = [repo['.'].node()]

    # We stop completely empty changesets prior to review.
    for rev in pushop.revs:
        ctx = repo[rev]
        if not ctx.files():
            raise util.Abort(_('not reviewing empty revision %s. please add'
                               ' content.' % hex(rev)[:12]))

    tipnode = None
    basenode = None

    # Our prepushoutgoing hook validates that all pushed changesets are
    # part of the same DAG head. If revisions were specified by the user,
    # the last is the tip commit to review and the first (if more than 1)
    # is the base commit to review.
    #
    # Note: the revisions are in the order they were specified by the user.
    # This may not be DAG order. So we have to explicitly order them here.
    revs = sorted(repo[r].rev() for r in pushop.revs)
    tipnode = repo[revs[-1]].node()
    if len(revs) > 1:
        basenode = repo[revs[0]].node()

    if repo.pushsingle:
        basenode = tipnode

    # Given a base and tip node, find all changesets to review.
    #
    # A solution that works most of the time is to find all non-public
    # ancestors of that node. This is our default.
    #
    # If basenode is specified, we stop the traversal when we encounter it.
    #
    # Note that we will still refuse to review a public changeset even with
    # basenode. This decision is somewhat arbitrary and can be revisited later
    # if there is an actual need to review public changesets.
    nodes = [tipnode]
    # Special case where basenode is the tip node.
    if basenode and tipnode == basenode:
        pass
    else:
        for node in repo[tipnode].ancestors():
            ctx = repo[node]

            if ctx.phase() == phases.public:
                break
            if basenode and ctx.node() == basenode:
                nodes.insert(0, ctx.node())
                break

            nodes.insert(0, ctx.node())

    # Filter out public nodes.
    publicnodes = []
    for node in nodes:
        ctx = repo[node]
        if ctx.phase() == phases.public:
            publicnodes.append(node)
            ui.status(_('(ignoring public changeset %s in review request)\n') %
                        ctx.hex()[0:12])

    nodes = [n for n in nodes if n not in publicnodes]
    if not nodes:
        raise util.Abort(
            _('no non-public changesets left to review'),
            hint=_('add or change the -r argument to include draft changesets'))

    # Ensure all reviewed changesets have commit IDs.
    replacenodes = []
    for node in nodes:
        ctx = repo[node]
        if 'commitid' not in ctx.extra():
            replacenodes.append(node)

    def addcommitid(repo, ctx, revmap, copyfilectxfn):
        parents = newparents(repo, ctx, revmap)
        # Need to make a copy otherwise modification is made on original,
        # which is just plain wrong.
        extra = dict(ctx.extra())
        assert 'commitid' not in extra
        extra['commitid'] = genid(repo)
        memctx = context.memctx(repo, parents,
                                ctx.description(), ctx.files(),
                                copyfilectxfn, user=ctx.user(),
                                date=ctx.date(), extra=extra)

        return memctx

    if replacenodes:
        ui.status(_('(adding commit id to %d changesets)\n') %
                  (len(replacenodes)))
        nodemap = replacechangesets(repo, replacenodes, addcommitid,
                                    backuptopic='addcommitid')

        # Since we're in the middle of an operation, update references
        # to rewritten nodes.
        nodes = [nodemap.get(node, node) for node in nodes]
        pushop.revs = [nodemap.get(node, node) for node in pushop.revs]

    pushop.reviewnodes = nodes

    # Since we may rewrite changesets to contain review metadata after
    # push, abort immediately if the working directory state is not
    # compatible with rewriting. This prevents us from successfully
    # pushing and failing to update commit metadata after the push. i.e.
    # it prevents potential loss of metadata.
    #
    # There may be some scenarios where we don't rewrite after push.
    # But coding that here would be complicated. And future server changes
    # may change things like review request mapping, which may invalidate
    # client assumptions. So always assume a rewrite is needed.
    impactedrevs = list(repo.revs('%ln::', nodes))
    if repo['.'].rev() in impactedrevs:
        cmdutil.checkunfinished(repo)
        cmdutil.bailifchanged(repo)

    return orig(pushop)

def wrappedpushbookmark(orig, pushop):
    """Wraps exchange._pushbookmark to also push a review."""
    result = orig(pushop)

    if not pushop.reviewnodes:
        return result

    # Because doreview may perform history rewriting, we can't call it
    # when a transaction is opened. Mercurial 3.3 switched behavior so
    # a transaction is active during most parts of push, including
    # exchange._pushbookmark. The differences in behavior can be unified
    # once we drop support for 3.2.
    if hasattr(pushop, 'trmanager') and pushop.trmanager:
        def ontrclose(tr):
            doreview(pushop.repo, pushop.ui, pushop.remote, pushop.reviewnodes)
        pushop.trmanager._tr.addpostclose('reviewboard.doreview', ontrclose)
    else:
        doreview(pushop.repo, pushop.ui, pushop.remote, pushop.reviewnodes)

    return result

def doreview(repo, ui, remote, nodes):
    """Do the work of submitting a review to a remote repo.

    :remote is a peerrepository.
    :nodes is a list of nodes to review.
    """
    assert nodes
    assert 'pushreview' in getreviewcaps(remote)

    bzauth = getbugzillaauth(ui)
    if not bzauth:
        ui.warn(_('Bugzilla credentials not available. Not submitting review.\n'))
        return

    identifier = None

    # The review identifier can come from a number of places. In order of
    # priority:
    # 1. --reviewid argument passed to push command
    # 2. The active bookmark
    # 3. The active branch (if it isn't default)
    # 4. A bug number extracted from commit messages

    if repo.reviewid:
        identifier = repo.reviewid

    # TODO The server currently requires a bug number for the identifier.
    # Pull bookmark and branch names in once allowed.
    #elif repo._bookmarkcurrent:
    #    identifier = repo._bookmarkcurrent
    #elif repo.dirstate.branch() != 'default':
    #    identifier = repo.dirstate.branch()

    if not identifier:
        for node in nodes:
            ctx = repo[node]
            bugs = parse_bugs(ctx.description())
            if bugs:
                identifier = 'bz://%s' % bugs[0]
                break

    identifier = ReviewID(identifier)

    if not identifier:
        ui.write(_('Unable to determine review identifier. Review '
            'identifiers are extracted from commit messages automatically. '
            'Try to begin one of your commit messages with "Bug XXXXXX -"\n'))
        return

    # Append irc nick to review identifier.
    # This is an ugly workaround to a limitation in ReviewBoard. RB doesn't
    # really support changing the owner of a review. It is doable, but no
    # history is stored and this leads to faulty attribution. More details
    # in bug 1034188.
    if not identifier.user:
        ircnick = ui.config('mozilla', 'ircnick', None)
        identifier.user = ircnick

    if hasattr(repo, 'mq'):
        for patch in repo.mq.applied:
            if patch.node in nodes:
                ui.warn(_('(You are using mq to develop patches. For the best '
                    'code review experience, use bookmark-based development '
                    'with changeset evolution. Read more at '
                    'http://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview-user.html)\n'))
                break

    lines = commonrequestlines(ui, bzauth)
    lines.append('reviewidentifier %s' % urllib.quote(identifier.full))

    reviews = repo.reviews
    oldparentid = reviews.findparentreview(identifier=identifier.full)

    # Include obsolescence data so server can make intelligent decisions.
    obsstore = repo.obsstore
    for node in nodes:
        lines.append('csetreview %s' % hex(node))
        precursors = [hex(n) for n in obsolete.allprecursors(obsstore, [node])]
        lines.append('precursors %s %s' % (hex(node), ' '.join(precursors)))

    ui.write(_('submitting %d changesets for review\n') % len(nodes))

    res = remote._call('pushreview', data='\n'.join(lines))
    lines = getpayload(res)

    newparentid = None
    nodereviews = {}
    reviewdata = {}

    for line in lines:
        t, d = line.split(' ', 1)

        if t == 'display':
            ui.write('%s\n' % d)
        elif t == 'error':
            raise util.Abort(d)
        elif t == 'parentreview':
            newparentid = d
            reviews.addparentreview(identifier.full, newparentid)
            reviewdata[newparentid] = {}
        elif t == 'csetreview':
            node, rid = d.split(' ', 1)
            node = bin(node)
            reviewdata[rid] = {}
            nodereviews[node] = rid
        elif t == 'reviewdata':
            rid, field, value = d.split(' ', 2)
            reviewdata[rid][field] = decodepossiblelistvalue(value)
        elif t == 'rburl':
            reviews.baseurl = d

    reviews.remoteurl = remote.url()

    for node, rid in nodereviews.items():
        reviews.addnodereview(node, rid, newparentid)

    reviews.write()
    for rid, data in reviewdata.iteritems():
        reviews.savereviewrequest(rid, data)

    havedraft = False

    ui.write('\n')
    for node in nodes:
        rid = nodereviews[node]
        ctx = repo[node]
        # Bug 1065024 use cmdutil.show_changeset() here.
        ui.write('changeset:  %s:%s\n' % (ctx.rev(), ctx.hex()[0:12]))
        ui.write('summary:    %s\n' % ctx.description().splitlines()[0])
        # We want to encourage people to use r? when asking for a review rather
        # than r=.
        if list(parse_requal_reviewers(ctx.description())):
            ui.warn(_('(It appears you are using r= to specify reviewers for a'
                ' patch under review. Please use r? to avoid ambiguity as to'
                ' whether or not review has been granted.)\n'))
        ui.write('review:     %s' % reviews.reviewurl(rid))
        if reviewdata[rid].get('public') == 'False':
            havedraft = True
            ui.write(' (draft)')
        ui.write('\n\n')

    ui.write(_('review id:  %s\n') % identifier.full)
    ui.write(_('review url: %s') % reviews.parentreviewurl(identifier.full))
    if reviewdata[newparentid].get('public', None) == 'False':
        havedraft = True
        ui.write(' (draft)')
    ui.write('\n')

    havereviewers = bool(nodes)
    for node in nodes:
        rd = reviewdata[nodereviews[node]]
        if not rd.get('reviewers', None):
            havereviewers = False
            break

    # Make it clear to the user that they need to take action in order for
    # others to see this review series.
    if havedraft:
        # If the series is ready for publishing, prompt the user to perform the
        # publishing.
        if havereviewers:
            caps = getreviewcaps(remote)
            if 'publish' in caps:
                ui.write('\n')
                publish = ui.promptchoice(
                    _('publish this review request now (Yn)? $$ &Yes $$ &No'))
                if publish == 0:
                    publishreviewrequests(ui, remote, bzauth, [newparentid])
                else:
                    ui.status(_('(visit review url to publish this review '
                                'series so others can see it)\n'))
            else:
                ui.status(_('(visit review url to publish this review series '
                            'so others can see it)\n'))
        else:
            ui.status(_('(review requests lack reviewers; visit review url '
                        'to assign reviewers and publish this series)\n'))

def publishreviewrequests(ui, remote, bzauth, rrids):
    """Publish an iterable of review requests."""
    lines = commonrequestlines(ui, bzauth)
    for rrid in rrids:
        lines.append('reviewid %s' % rrid)

    res = remote._call('publishreviewrequests', data='\n'.join(lines))
    lines = getpayload(res)
    errored = False

    for line in lines:
        k, v = line.split(' ', 1)
        if k == 'success':
            ui.status(_('(published review request %s)\n') % v)
        elif k == 'error':
            errored = True
            rrid, error = v.split(' ', 1)
            ui.warn(_('error publishing review request %s: %s\n') %
                    (rrid, error))

    if errored:
        ui.warn(_('(review requests not published; visit review url to '
                  'attempt publishing there)\n'))

def _pullreviews(repo):
    reviews = repo.reviews
    if not reviews.remoteurl:
        raise util.Abort(_("We don't know of any review servers. Try "
                           "creating a review first."))

    reviewdata = _pullreviewidentifiers(repo, sorted(reviews.identifiers))
    repo.ui.write(_('updated %d reviews\n') % len(reviewdata))

def _pullreviewidentifiers(repo, identifiers):
    """Pull down information for a list of review identifier strings.

    This will request the currently published data for a review identifier,
    including the mapping of commits to review request ids for all review
    requests that are currently part of the identifier.
    """
    reviews = repo.reviews

    # In the ideal world, we'd use RBTools to talk directly to the ReviewBoard
    # API. Unfortunately, the Mercurial distribution on Windows doesn't ship
    # with the json module. So, we proxy through the Mercurial server and have
    # it do all the heavy lifting.
    # FUTURE Hook up RBTools directly.
    remote = hg.peer(repo, {}, reviews.remoteurl)
    caps = getreviewcaps(remote)
    if 'pullreviews' not in caps:
        raise util.Abort('cannot pull code review metadata; '
                         'server lacks necessary features')

    lines = commonrequestlines(repo.ui)
    for identifier in identifiers:
        lines.append('reviewid %s' % identifier)

    res = remote._call('pullreviews', data='\n'.join(lines))
    lines = getpayload(res)

    reviewdata = {}

    for line in lines:
        t, d = line.split(' ', 1)

        if t == 'parentreview':
            identifier, parentid = map(urllib.unquote, d.split(' ', 2))
            reviewdata[parentid] = {}
        elif t == 'csetreview':
            parentid, node, rid = map(urllib.unquote, d.split(' ', 3))
            reviewdata[rid] = {}
        elif t == 'reviewdata':
            rid, field, value = map(urllib.unquote, d.split(' ', 3))
            reviewdata.setdefault(rid, {})[field] = decodepossiblelistvalue(value)
        elif t == 'error':
            raise util.Abort(d)
        else:
            raise util.Abort(_('unknown value in response payload: %s') % t)

    for rid, data in reviewdata.iteritems():
        reviews.savereviewrequest(rid, data)

    return reviewdata

class identifierrecord(object):
    """Describes a review identifier in the context of the store."""
    def __init__(self, parentrrid):
        """Create a new review identifier record.

        ``parentrrid`` is the review request id of the parent review for this
        review identifier.
        """
        self.parentrrid = parentrrid

class noderecord(object):
    """Describes a node in the context of the store."""
    def __init__(self, rrids=None, parentrrids=None):
        self.rrids = set()
        self.parentrrids = set()
        if rrids:
            self.rrids |= set(rrids)
        if parentrrids:
            self.parentrrids |= set(parentrrids)

class reviewstore(object):
    """Holds information about ongoing reviews.

    When we push and pull review information, we store that data in a local
    data store. This class interacts with that store.

    The file consists of newline delimited data. Each line begins with a
    data type followed by a space followed by the data for that type.
    The types are as follows:

    'u' - URL of the Review Board server associated with the reviews repository.

    'r' - The push path of the reviews repository.

    'p' - Maps review identifier to id of the associated parent review request.
          Format is "<identifier> <review-request-id>".

    'c' - Maps node to associated review request id. Format is
          "<node> <review-request-id>".

    'pc' - Maps node to review request id of the parent review request. This
           associates a commit to a specific review identifier. Format is
           "<node> <review-request-id>".
    """
    def __init__(self, repo):
        self._repo = repo
        self._vfs = scmutil.vfs(repo.vfs.join('reviewboard'), audit=False)

        # Maps review identifiers to identifierrecord instances.
        self._identifiers = {}
        # Maps parent review id to identifierrecord instances. Shares the same
        # object instances as _identifiers.
        self._prids = {}

        # Maps nodes to noderecord instances.
        self._nodes = {}

        self.baseurl = None
        self.remoteurl = None

        try:
            for line in repo.vfs('reviews'):
                line = line.strip()
                if not line:
                    continue

                fields = line.split(' ', 1)
                if len(fields) != 2:
                    repo.ui.warn(_('malformed line in reviews file: %r\n') %
                                   line)
                    continue

                t, d = fields

                # Identifier to parent review ID.
                if t == 'p':
                    ident, rrid = d.split(' ', 1)
                    r = identifierrecord(parentrrid=rrid)
                    self._identifiers[ident] = r
                    self._prids[rrid] = r
                # Node to review id.
                elif t == 'c':
                    node, rid = d.split(' ', 1)
                    assert len(node) == 40
                    r = self._nodes.setdefault(bin(node), noderecord())
                    r.rrids.add(rid)
                # Node to parent id.
                elif t == 'pc':
                    node, pid = d.split(' ', 1)
                    assert len(node) == 40
                    self._nodes[bin(node)].parentrrids.add(pid)
                elif t == 'u':
                    self.baseurl = d
                elif t == 'r':
                    self.remoteurl = d

        except IOError as inst:
            if inst.errno != errno.ENOENT:
                raise

    @property
    def identifiers(self):
        """Returns a set of all known review identifiers."""
        return set(self._identifiers.keys())

    def write(self):
        """Write the reviews file back to disk."""
        repo = self._repo

        wlock = repo.wlock()
        try:
            f = repo.vfs('reviews', 'w', atomictemp=True)

            if self.baseurl:
                f.write('u %s\n' % self.baseurl)
            if self.remoteurl:
                f.write('r %s\n' % self.remoteurl)

            for ident, r in sorted(self._identifiers.iteritems()):
                f.write('p %s %s\n' % (ident, r.parentrrid))
            for node, r in sorted(self._nodes.iteritems()):
                for rid in sorted(r.rrids):
                    f.write('c %s %s\n' % (hex(node), rid))
                for pid in sorted(r.parentrrids):
                    f.write('pc %s %s\n' % (hex(node), pid))

            f.close()
        finally:
            wlock.release()

    def savereviewrequest(self, rid, data):
        """Save metadata about an individual review request."""

        path = self._vfs.join('review/%s.state' % rid)
        lines = []
        for k, v in sorted(data.iteritems()):
            if isinstance(v, list):
                parts = [urllib.quote(p) for p in v]
                lines.append('%s %s' % (k, ','.join(parts)))
            else:
                lines.append('%s %s' % (k, urllib.quote(v)))

        self._vfs.write(path, '%s\n' % '\n'.join(lines))

    def getreviewrequest(self, rid):
        """Obtain metadata about a single review request."""
        path = self._vfs.join('review/%s.state' % rid)
        data = self._vfs.tryread(path)
        if not data:
            return None

        d = {}
        for line in data.splitlines():
            line = line.rstrip()
            if not line:
                continue

            k, v = line.split(' ', 1)
            if ',' in v:
                d[k] = [urllib.unquote(p) for p in v.split(',')]
            else:
                d[k] = urllib.unquote(v)

        return d

    def addparentreview(self, identifier, rrid):
        """Record the existence of a parent review."""
        self._identifiers[identifier] = identifierrecord(parentrrid=rrid)

    def addnodereview(self, node, rid, pid):
        """Record the existence of a review against a single node."""
        assert len(node) == 20
        assert pid
        r = self._nodes.setdefault(node, noderecord())
        r.rrids.add(rid)
        r.parentrrids.add(pid)

    def findnodereviews(self, node):
        """Find all reviews associated with a node."""
        assert len(node) == 20

        r = self._nodes.get(node)
        if r and r.rrids:
            return r.rrids

        return set()

    def findparentreview(self, identifier=None):
        """Find a parent review given some data."""

        if identifier:
            r = self._identifiers.get(identifier, None)
            if r:
                return r.parentrrid

        return None

    def parentreviewurl(self, identifier):
        """Obtain the URL associated with the review for an identifier."""
        r = self._identifiers.get(identifier, None)
        if not r:
            return None

        return '%s/r/%s' % (self.baseurl, r.parentrrid)

    def reviewurl(self, rid):
        """Obtain the URL associated with a review id."""
        return '%s/r/%s' % (self.baseurl, rid)

def template_reviews(repo, ctx, revcache, **args):
    """:reviews: List. Objects describing each review for this changeset."""
    if 'reviews' not in revcache:
        reviews = []
        for rid in sorted(repo.reviews.findnodereviews(ctx.node())):
            r = repo.reviews.getreviewrequest(rid)
            # Bug 1065022 add parent review info to this data structure.
            reviews.append({
                'url': repo.reviews.reviewurl(rid),
                'status': r.get('status'),
            })

        revcache['reviews'] = reviews
    return templatekw.showlist('review', revcache['reviews'])

@command('fetchreviews', [], _('hg fetchreviews'))
def fetchreviews(ui, repo, **opts):
    """Fetch information about your active code reviews.

    When you initiate a code review by pushing to a review-enabled remote,
    your repository will track the existence of that code review.

    This command is used to fetch code review information from a code review
    server into your local repository.
    """
    # Terminology around this feature uses "pull" because we eventually want
    # to work this into "hg pull."
    return _pullreviews(repo)

# The implementation of sshpeer.readerr() is buggy on Linux.
# See issue 4336 in Mercurial. This will likely get fixed in
# Mercurial 3.2. Work around it until we no longer support the
# buggy version.
def wrappedreaderr(orig, self):
    import fcntl
    flags = fcntl.fcntl(self.pipee, fcntl.F_GETFL)
    flags |= os.O_NONBLOCK
    oldflags = fcntl.fcntl(self.pipee, fcntl.F_SETFL, flags)

    chunks = []
    try:
        while True:
            try:
                s = self.pipee.read()
                if not s:
                    break
                chunks.append(s)
            except IOError:
                break
    finally:
        fcntl.fcntl(self.pipee, fcntl.F_SETFL, oldflags)

    for l in ''.join(chunks).splitlines():
        self.ui.status(_("remote: "), l, '\n')

def extsetup(ui):
    extensions.wrapfunction(exchange, 'push', wrappedpush)
    # Mercurial 3.2 introduces a decorator for registering functions to
    # be called during discovery. Switch to this once we drop support for
    # 3.1.
    extensions.wrapfunction(exchange, '_pushdiscovery', wrappedpushdiscovery)
    # _pushbookmark gets called near the end of push. Sadly, there isn't
    # a better place to hook that has access to the pushop.
    extensions.wrapfunction(exchange, '_pushbookmark', wrappedpushbookmark)

    if os.name == 'posix':
        extensions.wrapfunction(sshpeer.sshpeer, 'readerr', wrappedreaderr)

    # Define some extra arguments on the push command.
    entry = extensions.wrapcommand(commands.table, 'push', pushcommand)
    entry[1].append(('', 'noreview', False,
                     _('Do not perform a review on push.')))
    entry[1].append(('', 'reviewid', '', _('Review identifier')))
    entry[1].append(('c', 'changeset', '',
                    _('Review this specific changeset only')))

    templatekw.keywords['reviews'] = template_reviews

def reposetup(ui, repo):
    if not repo.local():
        return

    class reviewboardrepo(repo.__class__):
        @localrepo.repofilecache('reviews')
        def reviews(self):
            return reviewstore(self)

        def commit(self, *args, **kwargs):
            """Override commit to generate a unique commit identifier.

            The commit identifier is used to track a logical commits across
            history rewrites, including grafting. This is used as an index
            of sorts in the review tool.
            """
            # Some callers of commit() may not pass named arguments. Slurp
            # extra from positional arguments.
            if len(args) == 7:
                assert 'extra' not in kwargs
                kwargs['extra'] = args[6]
                args = tuple(args[0:5])

            extra = kwargs.setdefault('extra', {})
            if 'commitid' not in extra and self.reviews.remoteurl:
                extra['commitid'] = genid(self)

            return super(reviewboardrepo, self).commit(*args, **kwargs)

    repo.__class__ = reviewboardrepo
    repo.noreviewboardpush = False
    repo.reviewid = None

    def prepushoutgoinghook(local, remote, outgoing):
        if 'pushreview' in getreviewcaps(remote):
            # We can't simply look at outgoing.missingheads here because
            # Mercurial treats all revisions to `hg push` as "heads" in the
            # context of discovery. This is arguably a bug in Mercurial and may
            # be changed. This behavior was last observed in 3.2. So, in the
            # case of multiple missing heads, we run things through the DAG,
            # just in case.
            if len(outgoing.missingheads) > 1:
                # "%ln" is internal revset syntax for "a list of binary nodes."
                realmissingheads = local.revs('heads(%ln)',
                                              outgoing.missingheads)
                if len(realmissingheads) > 1:
                    raise util.Abort(_('cannot push multiple heads to remote; '
                        'limit pushed revisions using the -r argument.'))

    repo.prepushoutgoinghooks.add('reviewboard', prepushoutgoinghook)
