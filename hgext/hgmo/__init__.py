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

import collections
import hashlib
import json
import os
import subprocess
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

minimumhgversion = '4.8'
testedwith = '4.8 4.9 5.0'

cmdtable = {}

command = registrar.command(cmdtable)

configtable = {}
configitem = registrar.configitem(configtable)

configitem('mozilla', 'treeherder_repo',
           default=configitems.dynamicdefault)
configitem('hgmo', 'automationrelevantdraftancestors',
           default=configitems.dynamicdefault)
configitem('hgmo', 'backoutsearchlimit',
           default=configitems.dynamicdefault)
configitem('hgmo', 'convertsource',
           default=None)
configitem('hgmo', 'headdivergencemaxnodes',
           default=configitems.dynamicdefault)
configitem('hgmo', 'mozippath',
           default=None)
configitem('hgmo', 'awsippath',
           default=None)
configitem('hgmo', 'pullclonebundlesmanifest',
           default=configitems.dynamicdefault)
configitem('hgmo', 'replacebookmarks',
           default=configitems.dynamicdefault)

# TODO update this to /run/cloud-init/instance_data.json once
# we can upgrade cloud-init to 18.4+ on CentOS7
INSTANCE_DATA_PATH = '/var/hg/instance_data.json'


@templatefilters.templatefilter('mozlink')
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
            yield {
                'no': str(bug),
                'url': 'https://bugzilla.mozilla.org/show_bug.cgi?id=%s' % bug,
            }

    def reviewersgen(_context):
        '''Generator for reviewers list'''
        for reviewer in commitparser.parse_reviewers(description):
            yield {
                'name': reviewer,
                'revset': 'reviewer(%s)' % reviewer,
            }

    def backoutsgen(_context):
        '''Generator for backouts list'''
        backouts = commitparser.parse_backouts(description)
        if backouts:
            for node in backouts[0]:
                try:
                    bctx = scmutil.revsymbol(repo, node)
                    yield {'node': bctx.hex()}
                except error.RepoLookupError:
                    pass

    d['reviewers'] = templateutil.mappinggenerator(reviewersgen)
    d['bugs'] = templateutil.mappinggenerator(bugsgen)
    d['backsoutnodes'] = templateutil.mappinggenerator(backoutsgen)

    # Repositories can define which TreeHerder repository they are associated
    # with.
    treeherder = repo.ui.config('mozilla', 'treeherder_repo')
    if treeherder:
        d['treeherderrepourl'] = 'https://treeherder.mozilla.org/#/jobs?repo=%s' % treeherder
        d['treeherderrepo'] = treeherder

        push = repo.pushlog.pushfromchangeset(ctx)
        # Don't print Perfherder link on non-publishing repos (like Try)
        # because the previous push likely has nothing to do with this
        # push.
        # Changeset on autoland are in the phase 'draft' until they get merged
        # to mozilla-central.
        if push and push.nodes and (repo.ui.configbool('phases', 'publish', True) or treeherder == 'autoland'):
            lastpushhead = repo[push.nodes[0]].hex()
            d['perfherderurl'] = (
                'https://treeherder.mozilla.org/perf.html#/compare?'
                'originalProject=%s&'
                'originalRevision=%s&'
                'newProject=%s&'
                'newRevision=%s') % (treeherder, push.nodes[-1],
                                     treeherder, lastpushhead)

    # If this changeset was converted from another one and we know which repo
    # it came from, add that metadata.
    convertrevision = ctx.extra().get('convert_revision')
    if convertrevision:
        sourcerepo = repo.ui.config('hgmo', 'convertsource')
        if sourcerepo:
            d['convertsourcepath'] = sourcerepo
            d['convertsourcenode'] = convertrevision

    # Did the push to this repo included extra data about the automated landing
    # system used?
    # We omit the key if it has no value so that the 'json' filter function in
    # the map file will return null for the key's value.  Otherwise the filter
    # will return a JSON empty string, even for False-y values like None.
    landingsystem = ctx.extra().get('moz-landing-system')
    if landingsystem:
        d['landingsystem'] = landingsystem

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
        fctx = repo.filectx('config/milestone.txt', changeid=ctx.node())
        lines = fctx.data().splitlines()
        lines = [l for l in lines if not l.startswith('#') and l.strip()]

        if lines:
            d['milestone'] = lines[0].strip()
    except error.LookupError:
        pass

    backout_node = get_backoutbynode('hgmo', repo, ctx)
    if backout_node is not None:
        d['backedoutbynode'] = backout_node


def changesetentry(orig, web, ctx):
    """Wraps webutil.changesetentry to provide extra metadata."""
    d = orig(web, ctx)

    addmetadata(web.repo, ctx, d)
    return d


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

    if 'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate('error', error="missing parameter 'node'")
        else:
            return web.sendtemplate('error', error={'error': "missing parameter 'node'"})

    nodes = req.qsparams.getall('node')

    csets = []
    for node in nodes:
        ctx = scmutil.revsymbol(web.repo, node)
        csets.append({
            'rev': ctx.rev(),
            'node': ctx.hex(),
            'user': ctx.user(),
            'date': ctx.date(),
            'description': ctx.description(),
            'branch': ctx.branch(),
            'tags': ctx.tags(),
            'parents': [p.hex() for p in ctx.parents()],
            'children': [c.hex() for c in ctx.children()],
            'files': ctx.files(),
        })

    return web.sendtemplate('info', csets=templateutil.mappinglist(csets))


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

    if 'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate('error', error="missing parameter 'node'")
        else:
            return web.sendtemplate('error', error={'error': "missing parameter 'node'"})

    repo = web.repo

    paths = set(req.qsparams.getall('p'))
    basectx = scmutil.revsymbol(repo, req.qsparams['node'])

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
    maxnodes = repo.ui.configint('hgmo', 'headdivergencemaxnodes', 1000)
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

    return web.sendtemplate('headdivergence', commitsbehind=commitsbehind,
                filemerges=filemerges, filemergesignored=filemergesignored)


def automationrelevancewebcommand(web):
    req = web.req

    if 'node' not in req.qsparams:
        # TRACKING hg48
        if util.versiontuple(n=2) >= (4, 8):
            return web.sendtemplate('error', error="missing parameter 'node'")
        else:
            return web.sendtemplate('error', error={'error': "missing parameter 'node'"})

    repo = web.repo
    deletefields = {
        'bookmarks',
        'branch',
        'branches',
        'changelogtag',
        'child',
        'ctx',
        'inbranch',
        'instabilities',
        'obsolete',
        'parent',
        'phase',
        'succsandmarkers',
        'tags',
        'whyunstable',
    }

    csets = []
    # Query an unfiltered repo because sometimes automation wants to run against
    # changesets that have since become hidden. The response exposes whether the
    # requested node is visible, so consumers can make intelligent decisions
    # about what to do if the changeset isn't visible.
    urepo = repo.unfiltered()

    revs = list(urepo.revs('automationrelevant(%r)', req.qsparams['node']))

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
                del entry['pushnodes']
            except KeyError:
                pass

            # Some items in changelistentry are generators, which json.dumps()
            # can't handle. So we expand them.
            for k, v in entry.items():
                # "files" is a generator that attempts to call a template.
                # Don't even bother and just repopulate it.
                if k == 'files':
                    entry['files'] = sorted(ctx.files())
                elif k == 'allparents':
                    # TRACKING hg48
                    # generic template keyword args needed (context, mapping)
                    # they are not actually used, so `None, None` is sufficient
                    if util.versiontuple(n=2) >= (4, 8):
                        iterator = v(None, None).itermaps(ctx)
                    else:
                        iterator = v().itermaps(ctx)

                    entry['parents'] = [p['node'] for p in iterator]
                    del entry['allparents']
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
        visible = csets[-1]['node'] in repo
    else:
        visible = None

    data = {
        'changesets': templateutil.mappinglist(csets),
        'visible': visible,
    }

    return web.sendtemplate('automationrelevance', **data)


def isancestorwebcommand(web):
    """Determine whether a changeset is an ancestor of another."""
    req = web.req
    for k in ('head', 'node'):
        if k not in req.qsparams:
            raise ErrorResponse(HTTP_NOT_FOUND, "missing parameter '%s'" % k)

    head = req.qsparams['head']
    node = req.qsparams['node']

    try:
        headctx = scmutil.revsingle(web.repo, head)
    except error.RepoLookupError:
        raise ErrorResponse(HTTP_NOT_FOUND, 'unknown head revision %s' % head)

    try:
        testctx = scmutil.revsingle(web.repo, node)
    except error.RepoLookupError:
        raise ErrorResponse(HTTP_NOT_FOUND, 'unknown node revision %s' % node)

    testrev = testctx.rev()
    isancestor = False

    for rev in web.repo.changelog.ancestors([headctx.rev()], inclusive=True):
        if rev == testrev:
            isancestor = True
            break

    return web.sendtemplate('isancestor',
                            headnode=headctx.hex(),
                            testnode=testctx.hex(),
                            isancestor=isancestor)


def repoinfowebcommand(web):
    group_owner = repo_owner(web.repo)
    return web.sendtemplate('repoinfo',
                            archives=web.archivelist('tip'),
                            groupowner=group_owner)


def revset_reviewer(repo, subset, x):
    """``reviewer(REVIEWER)``

    Changesets reviewed by a specific person.
    """
    l = revset.getargs(x, 1, 1, 'reviewer requires one argument')
    n = encoding.lower(revset.getstring(l[0], 'reviewer requires a string'))

    # Do not use a matcher here because regular expressions are not safe
    # for remote execution and may DoS the server.
    def hasreviewer(r):
        for reviewer in commitparser.parse_reviewers(repo[r].description()):
            if encoding.lower(reviewer) == n:
                return True

        return False

    return subset.filter(hasreviewer)


def revset_automationrelevant(repo, subset, x):
    """``automationrelevant(set)``

    Changesets relevant to scheduling in automation.

    Given a revset that evaluates to a single revision, will return that
    revision and any ancestors that are part of the same push unioned with
    non-public ancestors.
    """
    s = revset.getset(repo, revset.fullreposet(repo), x)
    if len(s) > 1:
        raise error.Abort('can only evaluate single changeset')

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
    if repo.ui.configbool('hgmo', 'automationrelevantdraftancestors', False):
        for rev in repo.revs('::%d & not public()', ctx.rev()):
            revs.add(rev)

    return subset & revset.baseset(revs)


def bmupdatefromremote(orig, ui, repo, remotemarks, path, trfunc, explicit=()):
    """Custom bookmarks applicator that overwrites with remote state.

    The default bookmarks merging code adds divergence. When replicating from
    master to mirror, a bookmark force push could result in divergence on the
    mirror during `hg pull` operations. We install our own code that replaces
    the complicated merging algorithm with a simple "remote wins" version.
    """
    if not ui.configbool('hgmo', 'replacebookmarks', False):
        return orig(ui, repo, remotemarks, path, trfunc, explicit=explicit)

    localmarks = repo._bookmarks

    if localmarks == remotemarks:
        return

    ui.status('remote bookmarks changed; overwriting\n')
    localmarks.clear()
    for bm, node in remotemarks.items():
        localmarks[bm] = bin(node)
    tr = trfunc()
    localmarks.recordchange(tr)


def servehgmo(orig, ui, repo, *args, **kwargs):
    """Wraps commands.serve to provide --hgmo flag."""
    if kwargs.get('hgmo', False):
        kwargs['style'] = 'gitweb_mozilla'
        kwargs['templates'] = os.path.join(ROOT, 'hgtemplates')

        # ui.copy() is funky. Unless we do this, extension settings get
        # lost when calling hg.repository().
        ui = ui.copy()

        def setconfig(name, paths):
            ui.setconfig('extensions', name,
                         os.path.join(ROOT, 'hgext', *paths))

        setconfig('firefoxreleases', ['firefoxreleases'])
        setconfig('pushlog', ['pushlog'])
        setconfig('pushlog-feed', ['pushlog', 'feed.py'])

        ui.setconfig('web', 'logoimg', 'moz-logo-bw-rgb.svg')

        # Since new extensions may have been flagged for loading, we need
        # to obtain a new repo instance to a) trigger loading of these
        # extensions b) force extensions' reposetup function to run.
        repo = hg.repository(ui, repo.root)

    return orig(ui, repo, *args, **kwargs)


@command('mozbuildinfo', [
    ('r', 'rev', '.', _('revision to query'), _('REV')),
    ('', 'pipemode', False, _('accept arguments from stdin')),
    ], _('show files info from moz.build files'),
    optionalrepo=True)
def mozbuildinfocommand(ui, repo, *paths, **opts):
    # This module imports modules not available to the hgweb virtualenv.
    # Delay importing it so it doesn't interfere with operation outside the
    # moz.build evaluation context.
    import mozhg.mozbuildinfo as mozbuildinfo

    if opts['pipemode']:
        data = json.loads(ui.fin.read())

        repo = hg.repository(ui, path=bytes(data['repo']))
        ctx = scmutil.revsingle(repo, bytes(data['node']))

        paths = data['paths']
    else:
        ctx = scmutil.revsingle(repo, bytes(opts['rev']))

    try:
        d = mozbuildinfo.filesinfo(repo, ctx, paths=paths)
    except Exception as e:
        d = {'error': 'Exception reading moz.build info: %s' % str(e)}

    if not d:
        d = {'error': 'no moz.build info available'}

    # TODO send data to templater.
    # Use stable output and indentation to make testing easier.
    ui.write(json.dumps(d, indent=2, sort_keys=True))
    ui.write('\n')
    return


def wsgisendresponse(orig, self):
    for chunk in orig(self):
        if isinstance(chunk, bytearray):
            chunk = bytes(chunk)

        yield chunk


def pull(orig, repo, remote, *args, **kwargs):
    """Wraps exchange.pull to fetch the remote clonebundles.manifest."""
    res = orig(repo, remote, *args, **kwargs)

    if not repo.ui.configbool('hgmo', 'pullclonebundlesmanifest', False):
        return res

    has_clonebundles = remote.capable('clonebundles')
    if not has_clonebundles:
        if repo.vfs.exists('clonebundles.manifest'):
            repo.ui.status(_('deleting local clonebundles.manifest\n'))
            repo.vfs.unlink('clonebundles.manifest')

    has_cinnabarclone = remote.capable('cinnabarclone')
    if not has_cinnabarclone:
        if repo.vfs.exists('cinnabar.manifest'):
            repo.ui.status(_('deleting local cinnabar.manifest\n'))
            repo.vfs.unlink('cinnabar.manifest')

    if has_clonebundles or has_cinnabarclone:
        with repo.wlock():
            if has_clonebundles:
                repo.ui.status(_('pulling clonebundles manifest\n'))
                manifest = remote._call('clonebundles')
                repo.vfs.write('clonebundles.manifest', manifest)
            if has_cinnabarclone:
                repo.ui.status(_('pulling cinnabarclone manifest\n'))
                manifest = remote._call('cinnabarclone')
                repo.vfs.write('cinnabar.manifest', manifest)

    return res


def stream_clone_cmp(a, b):
    """Comparison function to prioritize stream bundles"""
    packed = 'BUNDLESPEC=none-packed1'

    if packed in a and packed not in b:
        return -1
    if packed in b and packed not in a:
        return 1

    return 0


def filter_manifest_for_aws_region(manifest, region):
    """Filter a clonebundles manifest by region

    The returned manifest will be sorted to prioritize clone bundles
    for the specified AWS region.
    """
    filtered = [l for l in manifest.data.splitlines() if 'ec2region=%s' % region in l]
    # No manifest entries for this region.
    if not filtered:
        return manifest

    # We prioritize stream clone bundles to AWS clients because they are
    # the fastest way to clone and we want our automation to be fast.
    filtered = sorted(filtered, cmp=stream_clone_cmp)

    # We got a match. Write out the filtered manifest (with a trailing newline).
    filtered.append('')
    return '\n'.join(filtered)


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

    # Get path for Mozilla, AWS network prefixes. Return if missing
    mozpath = repo.ui.config('hgmo', 'mozippath')
    awspath = repo.ui.config('hgmo', 'awsippath')
    if not awspath and not mozpath:
        return manifest

    # Mozilla's load balancers add a X-Cluster-Client-IP header to identify the
    # actual source IP, so prefer it.
    sourceip = proto._req.headers.get('X-CLUSTER-CLIENT-IP',
                                      proto._req.rawenv.get('REMOTE_ADDR'))


    if not sourceip:
        return manifest
    else:
        sourceip = ipaddress.IPv4Address(sourceip.decode('ascii'))

    # If the request originates from a private IP address, and we are running on
    # a cloud instance, we should be serving traffic to private instances in CI.
    # Grab the region from the instance_data.json object and serve the correct
    # manifest accordingly
    if sourceip.is_private and os.path.exists(INSTANCE_DATA_PATH):
        with open(INSTANCE_DATA_PATH, 'rb') as fh:
            instance_data = json.load(fh)

        region = instance_data['v1']['region']

        return filter_manifest_for_aws_region(manifest, region)

    # If the AWS IP file path is set and some line in the manifest includes an ec2 region,
    # we will check if the request came from AWS to server optimized bundles.
    if awspath and 'ec2region=' in manifest.data:
        try:
            with open(awspath, 'rb') as fh:
                awsdata = json.load(fh)

            for ipentry in awsdata['prefixes']:
                network = ipaddress.IPv4Network(ipentry['ip_prefix'])

                if sourceip not in network:
                    continue

                region = ipentry['region']

                return filter_manifest_for_aws_region(manifest, region)

        except Exception as e:
            repo.ui.log('hgmo', 'exception filtering bundle source IPs: %s\n', e)

    # Determine if source IP is in a Mozilla network, as we stream results to those addresses
    if mozpath:
        try:
            with open(mozpath, 'rb') as fh:
                mozdata = fh.read().splitlines()

            for ipentry in mozdata:
                network = ipaddress.IPv4Network(ipentry.decode('ascii'))

                # If the source IP is from a Mozilla network, prioritize stream bundles
                if sourceip in network:
                    origlines = sorted(manifest.data.splitlines(), cmp=stream_clone_cmp)
                    origlines.append('')
                    return '\n'.join(origlines)

        except Exception as e:
            repo.ui.log('hgmo', 'exception filtering bundle source IPs: %s\n', e)
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
                push = web.repo.pushlog.pushfromnode(bin(entry['node']))
                if push:
                    entry['pushid'] = push.pushid
                    entry['pushdate'] = dateutil.makedate(push.when)
                else:
                    entry['pushid'] = None
                    entry['pushdate'] = None

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


# TRACKING hg49 need a custom wire protocol command to serve cache files
# to facilitate faster partial clones.
@wireprotov2server.wireprotocommand(
    'mozrawcachefiles',
    args={
        'files': {
            'type': 'set',
            'default': lambda: set(),
            'example': [b'hgtagsfnodes', b'manifestlog'],
        },
    },
    permission='pull')
def mozrawcachefiles(repo, proto, files):
    from mercurial import cacheutil

    # We assume that this establishes a reasonable filter on cache
    # files and the data being exposed is not "private."
    cachefiles = cacheutil.cachetocopy(repo)

    sendfiles = []
    totalsize = 0

    for cache in cachefiles:
        if files and cache not in files:
            continue

        if not repo.cachevfs.exists(cache):
            continue

        data = repo.cachevfs.read(cache)

        sendfiles.append((b'cache', cache, data))
        totalsize += len(data)

    # The format is the same as the rawstorefiledata command.
    yield {
        b'filecount': len(sendfiles),
        b'totalsize': totalsize,
    }

    for location, name, data in sendfiles:
        yield {
            b'location': location,
            b'path': name,
            b'size': len(data),
        }

        yield wireprototypes.indefinitebytestringresponse([data])


# TRACKING hg49 filesdata command in 4.8 has bugs. We work around with custom
# command implementation.

def emitfilerevisions(repo, path, revisions, linknodes, fields):
    for revision in revisions:
        d = {
            b'node': revision.node,
        }

        if b'parents' in fields:
            d[b'parents'] = [revision.p1node, revision.p2node]

        if b'linknode' in fields:
            d[b'linknode'] = linknodes[revision.node]

        followingmeta = []
        followingdata = []

        if b'revision' in fields:
            if revision.revision is not None:
                followingmeta.append((b'revision', len(revision.revision)))
                followingdata.append(revision.revision)
            else:
                d[b'deltabasenode'] = revision.basenode
                followingmeta.append((b'delta', len(revision.delta)))
                followingdata.append(revision.delta)

        if followingmeta:
            d[b'fieldsfollowing'] = followingmeta

        yield d

        for extra in followingdata:
            yield extra


def filesdata(repo, proto, haveparents, fields, pathfilter, revisions):
    # TODO This should operate on a repo that exposes obsolete changesets. There
    # is a race between a client making a push that obsoletes a changeset and
    # another client fetching files data for that changeset. If a client has a
    # changeset, it should probably be allowed to access files data for that
    # changeset.

    outgoing = wireprotov2server.resolvenodes(repo, revisions)
    filematcher = wireprotov2server.makefilematcher(repo, pathfilter)

    # path -> {fnode: linknode}
    fnodes = collections.defaultdict(dict)

    # We collect the set of relevant file revisions by iterating the changeset
    # revisions and either walking the set of files recorded in the changeset
    # or by walking the manifest at that revision. There is probably room for a
    # storage-level API to request this data, as it can be expensive to compute
    # and would benefit from caching or alternate storage from what revlogs
    # provide.
    for node in outgoing:
        ctx = repo[node]
        mctx = ctx.manifestctx()
        md = mctx.read()

        if haveparents:
            checkpaths = ctx.files()
        else:
            checkpaths = md.keys()

        for path in checkpaths:
            fnode = md[path]

            if path in fnodes and fnode in fnodes[path]:
                continue

            if not filematcher(path):
                continue

            fnodes[path].setdefault(fnode, node)

    yield {
        b'totalpaths': len(fnodes),
        b'totalitems': sum(len(v) for v in fnodes.values())
    }

    for path, filenodes in sorted(fnodes.items()):
        try:
            store = wireprotov2server.getfilestore(repo, proto, path)
        except wireprotov2server.FileAccessError as e:
            raise error.WireprotoCommandError(e.msg, e.args)

        yield {
            b'path': path,
            b'totalitems': len(filenodes),
        }

        revisions = store.emitrevisions(filenodes.keys(),
                                        revisiondata=b'revision' in fields,
                                        assumehaveparentrevisions=haveparents)

        for o in emitfilerevisions(repo, path, revisions, filenodes, fields):
            yield o


def rawstorefiledata_cache_fn(repo, proto, cacher, **args):
    # Only cache if we request changelog + manifestlog with no path filter.
    # Caching is hard and restricting what is cached is safer.
    if set(args.get('files', [])) != {'changelog', 'manifestlog'}:
        return None

    if args.get('pathfilter'):
        return None

    state = {
        b'globalversion': wireprotov2server.GLOBAL_CACHE_VERSION,
        b'localversion': 'moz0',
        b'command': b'rawstorefiledata',
        # TODO this needs to change when we support different wire protocol
        # versions.
        b'mediatype': wireprotov2server.FRAMINGTYPE,
        b'version': wireprotov2server.HTTP_WIREPROTO_V2,
        b'repo': repo.root,
    }

    # Hashing the entire changelog could take a while, since it can be
    # dozens or hundreds of megabytes. As a proxy, we hash the first few
    # bytes of the changelog (to pull in revlog flags) and the DAG heads
    # in the changelog.
    cl = repo.unfiltered().changelog

    with cl.opener(cl.indexfile, 'rb') as fh:
        state[b'changeloghead'] = fh.read(32768)

    state[b'changelogheads'] = cl.heads()

    cacher.adjustcachekeystate(state)

    hasher = hashlib.sha1()
    for chunk in cborutil.streamencode(state):
        hasher.update(chunk)

    return pycompat.sysbytes(hasher.hexdigest())


def extsetup(ui):
    # TRACKING hg49 4.8 would emit bytearray instances against PEP-3333.
    extensions.wrapfunction(requestmod.wsgiresponse, 'sendresponse',
                            wsgisendresponse)

    extensions.wrapfunction(exchange, 'pull', pull)
    extensions.wrapfunction(webutil, 'changesetentry', changesetentry)
    extensions.wrapfunction(webutil, 'changelistentry', changelistentry)
    extensions.wrapfunction(bookmarks, 'updatefromremote', bmupdatefromremote)
    extensions.wrapfunction(webcommands, 'filelog', filelog)

    revset.symbols['reviewer'] = revset_reviewer
    revset.safesymbols.add('reviewer')

    revset.symbols['automationrelevant'] = revset_automationrelevant
    revset.safesymbols.add('automationrelevant')

    # Install IP filtering for bundle URLs.

    # Build-in command from core Mercurial.
    extensions.wrapcommand(wireprotov1server.commands, 'clonebundles', processbundlesmanifest)

    entry = extensions.wrapcommand(commands.table, 'serve', servehgmo)
    entry[1].append(('', 'hgmo', False,
                     'Run a server configured like hg.mozilla.org'))

    setattr(webcommands, 'info', infowebcommand)
    webcommands.__all__.append('info')

    setattr(webcommands, 'headdivergence', headdivergencewebcommand)
    webcommands.__all__.append('headdivergence')

    setattr(webcommands, 'automationrelevance', automationrelevancewebcommand)
    webcommands.__all__.append('automationrelevance')

    setattr(webcommands, 'isancestor', isancestorwebcommand)
    webcommands.__all__.append('isancestor')

    setattr(webcommands, 'repoinfo', repoinfowebcommand)
    webcommands.__all__.append('repoinfo')

    # TRACKING hg49 install custom filesdata command handler to work around bugs.
    wireprotov2server.COMMANDS[b'filesdata'].func = filesdata

    # Teach rawstorefiledata command to cache.
    wireprotov2server.COMMANDS[b'rawstorefiledata'].cachekeyfn = rawstorefiledata_cache_fn


def reposetup(ui, repo):
    fasupport = import_module('hgext.fastannotate.support')

    if not fasupport:
        return

    # fastannotate in Mercurial 4.8 has buggy hgweb support. We always remove
    # its monkeypatch if present.
    try:
        extensions.unwrapfunction(webutil, 'annotate',
                                  fasupport._hgwebannotate)
    except ValueError:
        pass

    # And we install our own if fastannotate is enabled.
    try:
        fastannotate = extensions.find('fastannotate')
    except KeyError:
        fastannotate = None

    if fastannotate and 'hgweb' in ui.configlist('fastannotate', 'modes'):
        # Guard against recursive chaining, since we're in reposetup().
        try:
            extensions.unwrapfunction(webutil, 'annotate',
                                      hgwebfastannotate)
        except ValueError:
            pass

        extensions.wrapfunction(webutil, 'annotate',
                                hgwebfastannotate)
