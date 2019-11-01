# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Provide enhancements to hg.mozilla.org

Config Options
==============

hgmo.replacebookmarks
   When set, `hg pull` and other bookmark application operations will replace
   local bookmarks with incoming bookmarks instead of doing the more
   complicated default behavior, which includes creating diverged bookmarks.

hgmo.convertsource
   When set and a changeset has a ``convert_revision`` extra data attribute,
   the changeset template data will contain a link to the source revision it
   was converted from.

   Value is a relative or absolute path to the repo. e.g.
   ``/mozilla-central``.
"""

import copy
import json
import os
import types

from mercurial.i18n import _
from mercurial.node import bin
from mercurial.utils import (
    cborutil,
    dateutil,
)
from mercurial import (
    bookmarks,
    commands,
    configitems,
    encoding,
    error,
    exchange,
    extensions,
    hg,
    pycompat,
    registrar,
    revset,
    scmutil,
    templatefilters,
    templateutil,
    util,
    wireprototypes,
    wireprotov1server,
    wireprotov2server,
)
from mercurial.hgweb import (
    request as requestmod,
    webcommands,
    webutil,
)
from mercurial.hgweb.common import (
    ErrorResponse,
    HTTP_NOT_FOUND,
)

OUR_DIR = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

import mozautomation.commitparser as commitparser
from mozhg.util import (
    import_module,
    repo_owner,
    get_backoutbynode,
)

from mercurial.wireprotoserver import httpv1protocolhandler as webproto

minimumhgversion = b'4.8'
testedwith = b'4.8 4.9 5.0 5.1'

cmdtable = {}

command = registrar.command(cmdtable)
revsetpredicate = registrar.revsetpredicate()

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'mozilla', b'treeherder_repo',
           default=configitems.dynamicdefault)
configitem(b'hgmo', b'automationrelevantdraftancestors',
           default=configitems.dynamicdefault)
configitem(b'hgmo', b'backoutsearchlimit',
           default=configitems.dynamicdefault)
configitem(b'hgmo', b'convertsource',
           default=None)
configitem(b'hgmo', b'headdivergencemaxnodes',
           default=configitems.dynamicdefault)
configitem(b'hgmo', b'mozippath',
           default=None)
configitem(b'hgmo', b'awsippath',
           default=None)
configitem(b'hgmo', b'gcpippath',
           default=None)
configitem(b'hgmo', b'pullclonebundlesmanifest',
           default=configitems.dynamicdefault)
configitem(b'hgmo', b'replacebookmarks',
           default=configitems.dynamicdefault)

# TODO update this to /run/cloud-init/instance_data.json once
# we can upgrade cloud-init to 18.4+ on CentOS7
INSTANCE_DATA_PATH = b'/var/hg/instance_data.json'


@templatefilters.templatefilter(b'mozlink')
def mozlink(text):
    """Any text. Hyperlink to Bugzilla and other detected things."""
    return commitparser.add_hyperlinks(text)


def stream_json(data):
    """Convert a data structure to a generator of chunks representing JSON."""
    # We use latin1 as the encoding because all data should be treated as
    # byte strings. ensure_ascii will escape non-ascii values using \uxxxx.
    # Also, use stable output and indentation to make testing easier.
    encoder = json.JSONEncoder(indent=2, sort_keys=True, encoding='latin1',
                               separators=(',', ': '))
    return encoder.iterencode(data)


def addmetadata(repo, ctx, d, onlycheap=False):
    """Add changeset metadata for hgweb templates."""
    description = encoding.fromlocal(ctx.description())

    def bugsgen(_context):
        '''Generator for bugs list'''
        for bug in commitparser.parse_bugs(description):
            bug = pycompat.bytestr(bug)
            yield {
                b'no': bug,
                b'url': b'https://bugzilla.mozilla.org/show_bug.cgi?id=%s' % bug,
            }

    def reviewersgen(_context):
        '''Generator for reviewers list'''
        for reviewer in commitparser.parse_reviewers(description):
            yield {
                b'name': reviewer,
                b'revset': b'reviewer(%s)' % reviewer,
            }

    def backoutsgen(_context):
        '''Generator for backouts list'''
        backouts = commitparser.parse_backouts(description)
        if backouts:
            for node in backouts[0]:
                try:
                    bctx = scmutil.revsymbol(repo, node)
                    yield {b'node': bctx.hex()}
                except error.RepoLookupError:
                    pass

    d[b'reviewers'] = templateutil.mappinggenerator(reviewersgen)
    d[b'bugs'] = templateutil.mappinggenerator(bugsgen)
    d[b'backsoutnodes'] = templateutil.mappinggenerator(backoutsgen)

    # Repositories can define which TreeHerder repository they are associated
    # with.
    treeherder = repo.ui.config(b'mozilla', b'treeherder_repo')
    if treeherder:
        d[b'treeherderrepourl'] = b'https://treeherder.mozilla.org/#/jobs?repo=%s' % treeherder
        d[b'treeherderrepo'] = treeherder

        push = repo.pushlog.pushfromchangeset(ctx)
        # Don't print Perfherder link on non-publishing repos (like Try)
        # because the previous push likely has nothing to do with this
        # push.
        # Changeset on autoland are in the phase 'draft' until they get merged
        # to mozilla-central.
        if push and push.nodes and (repo.ui.configbool(b'phases', b'publish', True) or treeherder == b'autoland'):
            lastpushhead = repo[push.nodes[0]].hex()
            d[b'perfherderurl'] = (
                b'https://treeherder.mozilla.org/perf.html#/compare?'
                b'originalProject=%s&'
                b'originalRevision=%s&'
                b'newProject=%s&'
                b'newRevision=%s') % (treeherder, push.nodes[-1],
                                      treeherder, lastpushhead)

    # If this changeset was converted from another one and we know which repo
    # it came from, add that metadata.
    convertrevision = ctx.extra().get(b'convert_revision')
    if convertrevision:
        sourcerepo = repo.ui.config(b'hgmo', b'convertsource')
        if sourcerepo:
            d[b'convertsourcepath'] = sourcerepo
            d[b'convertsourcenode'] = convertrevision

    # Did the push to this repo included extra data about the automated landing
    # system used?
    # We omit the key if it has no value so that the 'json' filter function in
    # the map file will return null for the key's value.  Otherwise the filter
    # will return a JSON empty string, even for False-y values like None.
    landingsystem = ctx.extra().get(b'moz-landing-system')
    if landingsystem:
        d[b'landingsystem'] = landingsystem

    if onlycheap:
        return

    # Obtain the Gecko/app version/milestone.
    #
    # We could probably only do this if the repo is a known app repo (by
    # looking at the initial changeset). But, path based lookup is relatively
    # fast, so just do it. However, we need this in the "onlycheap"
    # section because resolving manifests is relatively slow and resolving
    # several on changelist pages may add seconds to page load times.
    try:
        fctx = repo.filectx(b'config/milestone.txt', changeid=ctx.node())
        lines = fctx.data().splitlines()
        lines = [l for l in lines if not l.startswith(b'#') and l.strip()]

        if lines:
            d[b'milestone'] = lines[0].strip()
    except error.LookupError:
        pass

    backout_node = get_backoutbynode(b'hgmo', repo, ctx)
    if backout_node is not None:
        d[b'backedoutbynode'] = backout_node


def changesetentry(orig, web, ctx):
    """Wraps webutil.changesetentry to provide extra metadata."""
    d = orig(web, ctx)

    d = pycompat.byteskwargs(d)

    addmetadata(web.repo, ctx, d)

    return pycompat.strkwargs(d)


def changelistentry(orig, web, ctx):
    """Wraps webutil.changelistentry to provide extra metadata."""
    d = orig(web, ctx)

    addmetadata(web.repo, ctx, d, onlycheap=True)
    return d


def infowebcommand(web):
    """Get information about the specified changeset(s).

    This is a legacy API from before the days of Mercurial's built-in JSON
    API. It is used by unidentified parts of automation. Over time these
    consumers should transition to the modern/native JSON API.
    """
    req = web.req

    if b'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate(b'error', error=b"missing parameter 'node'")
        else:
            return web.sendtemplate(b'error', error={b'error': b"missing parameter 'node'"})

    nodes = req.qsparams.getall(b'node')

    csets = []
    for node in nodes:
        ctx = scmutil.revsymbol(web.repo, node)
        csets.append({
            b'rev': ctx.rev(),
            b'node': ctx.hex(),
            b'user': ctx.user(),
            b'date': ctx.date(),
            b'description': ctx.description(),
            b'branch': ctx.branch(),
            b'tags': ctx.tags(),
            b'parents': [p.hex() for p in ctx.parents()],
            b'children': [c.hex() for c in ctx.children()],
            b'files': ctx.files(),
        })

    return web.sendtemplate(b'info', csets=templateutil.mappinglist(csets))


def headdivergencewebcommand(web):
    """Get information about divergence between this repo and a changeset.

    This API was invented to be used by MozReview to obtain information about
    how a repository/head has progressed/diverged since a commit was submitted
    for review.

    It is assumed that this is running on the canonical/mainline repository.
    Changes in other repositories must be rebased onto or merged into
    this repository.
    """
    req = web.req

    if b'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate(b'error', error=b"missing parameter 'node'")
        else:
            return web.sendtemplate(b'error', error={b'error': b"missing parameter 'node'"})

    repo = web.repo

    paths = set(req.qsparams.getall(b'p'))
    basectx = scmutil.revsymbol(repo, req.qsparams[b'node'])

    # Find how much this repo has changed since the requested changeset.
    # Our heuristic is to find the descendant head with the highest revision
    # number. Most (all?) repositories we care about for this API should have
    # a single head per branch. And we assume the newest descendant head is
    # the one we care about the most. We don't care about branches because
    # if a descendant is on different branch, then the repo has likely
    # transitioned to said branch.
    #
    # If we ever consolidate Firefox repositories, we'll need to reconsider
    # this logic, especially if release repos with their extra branches/heads
    # are involved.

    # Specifying "start" only gives heads that are descendants of "start."
    headnodes = repo.changelog.heads(start=basectx.node())

    headrev = max(repo[n].rev() for n in headnodes)
    headnode = repo[headrev].node()

    betweennodes, outroots, outheads = \
        repo.changelog.nodesbetween([basectx.node()], [headnode])

    # nodesbetween returns base node. So prune.
    betweennodes = betweennodes[1:]

    commitsbehind = len(betweennodes)

    # If rev 0 or a really old revision is passed in, we could DoS the server
    # by having to iterate nearly all changesets. Establish a cap for number
    # of changesets to examine.
    maxnodes = repo.ui.configint(b'hgmo', b'headdivergencemaxnodes', 1000)
    filemergesignored = False
    if len(betweennodes) > maxnodes:
        betweennodes = []
        filemergesignored = True

    filemerges = {}
    for node in betweennodes:
        ctx = repo[node]

        files = set(ctx.files())
        for p in files & paths:
            filemerges.setdefault(p, []).append(ctx.hex())

    return web.sendtemplate(b'headdivergence', commitsbehind=commitsbehind,
                filemerges=filemerges, filemergesignored=filemergesignored)


def automationrelevancewebcommand(web):
    req = web.req

    if b'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate(b'error', error=b"missing parameter 'node'")
        else:
            return web.sendtemplate(b'error', error={b'error': b"missing parameter 'node'"})

    repo = web.repo
    deletefields = {
        b'bookmarks',
        b'branch',
        b'branches',
        b'changelogtag',
        b'child',
        b'ctx',
        b'inbranch',
        b'instabilities',
        b'obsolete',
        b'parent',
        b'phase',
        b'succsandmarkers',
        b'tags',
        b'whyunstable',
    }

    csets = []
    # Query an unfiltered repo because sometimes automation wants to run against
    # changesets that have since become hidden. The response exposes whether the
    # requested node is visible, so consumers can make intelligent decisions
    # about what to do if the changeset isn't visible.
    urepo = repo.unfiltered()

    revs = list(urepo.revs(b'automationrelevant(%r)', req.qsparams[b'node']))

    # The pushlog extensions wraps webutil.commonentry and the way it is called
    # means pushlog opens a SQLite connection on every call. This is inefficient.
    # So we pre load and cache data for pushlog entries we care about.
    cl = urepo.changelog
    nodes = [cl.node(rev) for rev in revs]

    with repo.unfiltered().pushlog.cache_data_for_nodes(nodes):
        for rev in revs:
            ctx = urepo[rev]
            entry = webutil.changelistentry(web, ctx)

            # The pushnodes list is redundant with data from other changesets.
            # The amount of redundant data for pushes containing N>100
            # changesets can add up to megabytes in size.
            try:
                del entry[b'pushnodes']
            except KeyError:
                pass

            # Some items in changelistentry are generators, which json.dumps()
            # can't handle. So we expand them.
            entrycopy = copy.copy(entry)
            for k, v in entrycopy.items():
                # "files" is a generator that attempts to call a template.
                # Don't even bother and just repopulate it.
                if k == b'files':
                    entry[b'files'] = sorted(ctx.files())
                elif k == b'allparents':
                    # TRACKING hg48
                    # generic template keyword args needed (context, mapping)
                    # they are not actually used, so `None, None` is sufficient
                    if util.versiontuple(n=2) >= (4, 8):
                        iterator = v(None, None).itermaps(ctx)
                    else:
                        iterator = v().itermaps(ctx)

                    entry[b'parents'] = [p[b'node'] for p in iterator]
                    del entry[b'allparents']
                # These aren't interesting to us, so prune them. The
                # original impetus for this was because "changelogtag"
                # isn't part of the json template and adding it is non-trivial.
                elif k in deletefields:
                    del entry[k]
                elif isinstance(v, types.GeneratorType):
                    entry[k] = list(v)

            csets.append(entry)

    # Advertise whether the requested revision is visible (non-obsolete).
    if csets:
        visible = csets[-1][b'node'] in repo
    else:
        visible = None

    data = {
        b'changesets': templateutil.mappinglist(csets),
        b'visible': visible,
    }

    return web.sendtemplate(b'automationrelevance', **pycompat.strkwargs(data))


def isancestorwebcommand(web):
    """Determine whether a changeset is an ancestor of another."""
    req = web.req
    for k in (b'head', b'node'):
        if k not in req.qsparams:
            raise ErrorResponse(HTTP_NOT_FOUND, b"missing parameter '%s'" % k)

    head = req.qsparams[b'head']
    node = req.qsparams[b'node']

    try:
        headctx = scmutil.revsingle(web.repo, head)
    except error.RepoLookupError:
        raise ErrorResponse(HTTP_NOT_FOUND, b'unknown head revision %s' % head)

    try:
        testctx = scmutil.revsingle(web.repo, node)
    except error.RepoLookupError:
        raise ErrorResponse(HTTP_NOT_FOUND, b'unknown node revision %s' % node)

    testrev = testctx.rev()
    isancestor = False

    for rev in web.repo.changelog.ancestors([headctx.rev()], inclusive=True):
        if rev == testrev:
            isancestor = True
            break

    return web.sendtemplate(b'isancestor',
                            headnode=headctx.hex(),
                            testnode=testctx.hex(),
                            isancestor=isancestor)


def repoinfowebcommand(web):
    group_owner = repo_owner(web.repo)
    return web.sendtemplate(b'repoinfo',
                            archives=web.archivelist(b'tip'),
                            groupowner=group_owner)


@revsetpredicate(b'reviewer(REVIEWER)', safe=True)
def revset_reviewer(repo, subset, x):
    """``reviewer(REVIEWER)``

    Changesets reviewed by a specific person.
    """
    l = revset.getargs(x, 1, 1, b'reviewer requires one argument')
    n = encoding.lower(revset.getstring(l[0], b'reviewer requires a string'))

    # Do not use a matcher here because regular expressions are not safe
    # for remote execution and may DoS the server.
    def hasreviewer(r):
        for reviewer in commitparser.parse_reviewers(repo[r].description()):
            if encoding.lower(reviewer) == n:
                return True

        return False

    return subset.filter(hasreviewer)


@revsetpredicate(b'automationrelevant(set)', safe=True)
def revset_automationrelevant(repo, subset, x):
    """``automationrelevant(set)``

    Changesets relevant to scheduling in automation.

    Given a revset that evaluates to a single revision, will return that
    revision and any ancestors that are part of the same push unioned with
    non-public ancestors.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    if len(s) > 1:
        raise error.Abort(b'can only evaluate single changeset')

    ctx = repo[s.first()]
    revs = {ctx.rev()}

    # The pushlog is used to get revisions part of the same push as
    # the requested revision.
    pushlog = getattr(repo, 'pushlog', None)
    if pushlog:
        push = repo.pushlog.pushfromchangeset(ctx)
        for n in push.nodes:
            pctx = repo[n]
            if pctx.rev() <= ctx.rev():
                revs.add(pctx.rev())

    # Union with non-public ancestors if configured. By default, we only
    # consider changesets from the push. However, on special repositories
    # (namely Try), we want changesets from previous pushes to come into
    # play too.
    if repo.ui.configbool(b'hgmo', b'automationrelevantdraftancestors', False):
        for rev in repo.revs(b'::%d & not public()', ctx.rev()):
            revs.add(rev)

    return subset & revset.baseset(revs)


def bmupdatefromremote(orig, ui, repo, remotemarks, path, trfunc, explicit=()):
    """Custom bookmarks applicator that overwrites with remote state.

    The default bookmarks merging code adds divergence. When replicating from
    master to mirror, a bookmark force push could result in divergence on the
    mirror during `hg pull` operations. We install our own code that replaces
    the complicated merging algorithm with a simple "remote wins" version.
    """
    if not ui.configbool(b'hgmo', b'replacebookmarks', False):
        return orig(ui, repo, remotemarks, path, trfunc, explicit=explicit)

    localmarks = repo._bookmarks

    if localmarks == remotemarks:
        return

    ui.status(b'remote bookmarks changed; overwriting\n')
    localmarks.clear()
    for bm, node in remotemarks.items():
        localmarks[bm] = bin(node)
    tr = trfunc()
    localmarks.recordchange(tr)


def servehgmo(orig, ui, repo, *args, **kwargs):
    """Wraps commands.serve to provide --hgmo flag."""
    if kwargs.get('hgmo', False):
        kwargs['style'] = b'gitweb_mozilla'
        kwargs['templates'] = os.path.join(pycompat.bytestr(ROOT), b'hgtemplates')

        # ui.copy() is funky. Unless we do this, extension settings get
        # lost when calling hg.repository().
        ui = ui.copy()

        def setconfig(name, paths):
            ui.setconfig(b'extensions', name,
                         os.path.join(pycompat.bytestr(ROOT), b'hgext', *paths))

        setconfig(b'firefoxreleases', [b'firefoxreleases'])
        setconfig(b'pushlog', [b'pushlog'])
        setconfig(b'pushlog-feed', [b'pushlog', b'feed.py'])

        ui.setconfig(b'web', b'logoimg', b'moz-logo-bw-rgb.svg')

        # Since new extensions may have been flagged for loading, we need
        # to obtain a new repo instance to a) trigger loading of these
        # extensions b) force extensions' reposetup function to run.
        repo = hg.repository(ui, repo.root)

    return orig(ui, repo, *args, **kwargs)


def pull(orig, repo, remote, *args, **kwargs):
    """Wraps exchange.pull to fetch the remote clonebundles.manifest."""
    res = orig(repo, remote, *args, **kwargs)

    if not repo.ui.configbool(b'hgmo', b'pullclonebundlesmanifest', False):
        return res

    has_clonebundles = remote.capable(b'clonebundles')
    if not has_clonebundles:
        if repo.vfs.exists(b'clonebundles.manifest'):
            repo.ui.status(_(b'deleting local clonebundles.manifest\n'))
            repo.vfs.unlink(b'clonebundles.manifest')

    has_cinnabarclone = remote.capable(b'cinnabarclone')
    if not has_cinnabarclone:
        if repo.vfs.exists(b'cinnabar.manifest'):
            repo.ui.status(_(b'deleting local cinnabar.manifest\n'))
            repo.vfs.unlink(b'cinnabar.manifest')

    if has_clonebundles or has_cinnabarclone:
        with repo.wlock():
            if has_clonebundles:
                repo.ui.status(_(b'pulling clonebundles manifest\n'))
                manifest = remote._call(b'clonebundles')
                repo.vfs.write(b'clonebundles.manifest', manifest)
            if has_cinnabarclone:
                repo.ui.status(_(b'pulling cinnabarclone manifest\n'))
                manifest = remote._call(b'cinnabarclone')
                repo.vfs.write(b'cinnabar.manifest', manifest)

    return res


def stream_clone_cmp(a, b):
    """Comparison function to prioritize stream bundles"""
    packed = b'BUNDLESPEC=none-packed1'

    if packed in a and packed not in b:
        return -1
    if packed in b and packed not in a:
        return 1

    return 0


# TRACKING py3 - `cmp` sorting function deprecated, use `key`
if pycompat.ispy3:
    import functools
    sorted_kwargs = {
        'key': functools.cmp_to_key(stream_clone_cmp),
    }
else:
    sorted_kwargs = {
        'cmp': stream_clone_cmp,
    }


def filter_manifest_for_region(manifest, region):
    """Filter a clonebundles manifest by region

    The returned manifest will be sorted to prioritize clone bundles
    for the specified AWS region.
    """
    filtered = [l for l in manifest.data.splitlines() if region in l]
    # No manifest entries for this region.
    if not filtered:
        return manifest

    # We prioritize stream clone bundles to AWS clients because they are
    # the fastest way to clone and we want our automation to be fast.
    filtered = sorted(filtered, **sorted_kwargs)

    # We got a match. Write out the filtered manifest (with a trailing newline).
    filtered.append(b'')
    return b'\n'.join(filtered)


def processbundlesmanifest(orig, repo, proto):
    """Wraps wireproto.clonebundles.

    We examine source IP addresses and advertise URLs for the same
    AWS region if the source is in AWS.
    """
    # Delay import because this extension can be run on local
    # developer machines.
    import ipaddress

    # Call original fxn wireproto.clonebundles
    manifest = orig(repo, proto)

    if not isinstance(proto, webproto):
        return manifest

    # Get path for Mozilla, AWS, GCP network prefixes. Return if missing
    mozpath = repo.ui.config(b'hgmo', b'mozippath')
    awspath = repo.ui.config(b'hgmo', b'awsippath')
    gcppath = repo.ui.config(b'hgmo', b'gcpippath')
    if not awspath and not mozpath and not gcppath:
        return manifest

    # Mozilla's load balancers add a X-Cluster-Client-IP header to identify the
    # actual source IP, so prefer it.
    sourceip = proto._req.headers.get(b'X-CLUSTER-CLIENT-IP',
                                      proto._req.rawenv.get(b'REMOTE_ADDR'))

    if not sourceip:
        return manifest
    else:
        sourceip = ipaddress.IPv4Address(pycompat.unicode(pycompat.sysstr(sourceip)))

    # If the request originates from a private IP address, and we are running on
    # a cloud instance, we should be serving traffic to private instances in CI.
    # Grab the region from the instance_data.json object and serve the correct
    # manifest accordingly
    if sourceip.is_private and os.path.exists(INSTANCE_DATA_PATH):
        with open(INSTANCE_DATA_PATH, 'rb') as fh:
            instance_data = json.load(fh)

        region = instance_data['v1']['region']

        return filter_manifest_for_region(manifest, b'ec2region=%s' % region)

    # If the AWS IP file path is set and some line in the manifest includes an ec2 region,
    # we will check if the request came from AWS to server optimized bundles.
    if awspath and b'ec2region=' in manifest.data:
        try:
            with open(awspath, 'rb') as fh:
                awsdata = json.load(fh)

            for ipentry in awsdata['prefixes']:
                network = ipaddress.IPv4Network(ipentry['ip_prefix'])

                if sourceip not in network:
                    continue

                region = ipentry['region']

                return filter_manifest_for_region(manifest, b'ec2region=%s' % region)

        except Exception as e:
            repo.ui.log(b'hgmo', b'exception filtering AWS bundle source IPs: %s\n', e)

    # If the GCP IP file path is set and some line in the manifest includes a GCE region,
    # we will check if the request came from GCP to serve optimized bundles
    if gcppath and b'gceregion=' in manifest.data:
        try:
            with open(gcppath, 'rb') as f:
                gcpdata = f.read().splitlines()

            for entry in gcpdata:
                network = ipaddress.IPv4Network(pycompat.unicode(entry))

                if sourceip not in network:
                    continue

                return filter_manifest_for_region(manifest, b'gceregion=us-central1')

        except Exception as e:
            repo.ui.log(b'hgmo', b'exception filtering GCP bundle source IPs: %s\n', e)

    # Determine if source IP is in a Mozilla network, as we stream results to those addresses
    if mozpath:
        try:
            with open(mozpath, 'r') as fh:
                mozdata = fh.read().splitlines()

            for ipentry in mozdata:
                network = ipaddress.IPv4Network(pycompat.unicode(pycompat.sysstr(ipentry)))

                # If the source IP is from a Mozilla network, prioritize stream bundles
                if sourceip in network:
                    origlines = sorted(manifest.data.splitlines(), **sorted_kwargs)
                    origlines.append(b'')
                    return b'\n'.join(origlines)

        except Exception as e:
            repo.ui.log(b'hgmo', b'exception filtering bundle source IPs: %s\n', e)
            return manifest

    return manifest


def filelog(orig, web):
    """Wraps webcommands.filelog to provide pushlog metadata to template."""
    req = web.req
    tmpl = web.templater(req)

    # Template wrapper to add pushlog data to entries when the template is
    # evaluated.
    class tmplwrapper(tmpl.__class__):
        def __call__(self, *args, **kwargs):
            for entry in kwargs.get('entries', []):
                push = web.repo.pushlog.pushfromnode(bin(entry[b'node']))
                if push:
                    entry[b'pushid'] = push.pushid
                    entry[b'pushdate'] = dateutil.makedate(push.when)
                else:
                    entry[b'pushid'] = None
                    entry[b'pushdate'] = None

            return super(tmplwrapper, self).__call__(*args, **kwargs)

    orig_class = tmpl.__class__
    try:
        if hasattr(web.repo, 'pushlog'):
            tmpl.__class__ = tmplwrapper

        web.tmpl = tmpl
        for r in orig(web):
            yield r
    finally:
        tmpl.__class__ = orig_class


def hgwebfastannotate(orig, req, fctx, ui):
    import hgext.fastannotate.support as fasupport

    diffopts = webutil.difffeatureopts(req, ui, 'annotate')

    return fasupport._doannotate(fctx, diffopts=diffopts)


def extsetup(ui):
    extensions.wrapfunction(exchange, b'pull', pull)
    extensions.wrapfunction(webutil, b'changesetentry', changesetentry)
    extensions.wrapfunction(webutil, b'changelistentry', changelistentry)
    extensions.wrapfunction(bookmarks, b'updatefromremote', bmupdatefromremote)
    extensions.wrapfunction(webcommands, b'filelog', filelog)

    # Install IP filtering for bundle URLs.

    # Build-in command from core Mercurial.
    extensions.wrapcommand(wireprotov1server.commands, b'clonebundles', processbundlesmanifest)

    entry = extensions.wrapcommand(commands.table, b'serve', servehgmo)
    entry[1].append((b'', b'hgmo', False,
                     b'Run a server configured like hg.mozilla.org'))

    setattr(webcommands, 'info', infowebcommand)
    webcommands.__all__.append(b'info')

    setattr(webcommands, 'headdivergence', headdivergencewebcommand)
    webcommands.__all__.append(b'headdivergence')

    setattr(webcommands, 'automationrelevance', automationrelevancewebcommand)
    webcommands.__all__.append(b'automationrelevance')

    setattr(webcommands, 'isancestor', isancestorwebcommand)
    webcommands.__all__.append(b'isancestor')

    setattr(webcommands, 'repoinfo', repoinfowebcommand)
    webcommands.__all__.append(b'repoinfo')


def reposetup(ui, repo):
    fasupport = import_module('hgext.fastannotate.support')

    if not fasupport:
        return

    # fastannotate in Mercurial 4.8 has buggy hgweb support. We always remove
    # its monkeypatch if present.
    try:
        extensions.unwrapfunction(webutil, b'annotate',
                                  fasupport._hgwebannotate)
    except ValueError:
        pass

    # And we install our own if fastannotate is enabled.
    try:
        fastannotate = extensions.find(b'fastannotate')
    except KeyError:
        fastannotate = None

    if fastannotate and b'hgweb' in ui.configlist(b'fastannotate', b'modes'):
        # Guard against recursive chaining, since we're in reposetup().
        try:
            extensions.unwrapfunction(webutil, b'annotate',
                                      hgwebfastannotate)
        except ValueError:
            pass

        extensions.wrapfunction(webutil, b'annotate',
                                hgwebfastannotate)
