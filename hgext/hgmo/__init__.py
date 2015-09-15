# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Provide enhancements to hg.mozilla.org

Config Options
==============

hgmo.mozbuildinfoenabled
   Whether evaluation of moz.build files for metadata is enabled from hgweb
   requests. This is disabled by default.

hgmo.mozbuildinfowrapper
   A command to execute to obtain moz.build file info.

   The value MUST not contain any quote characters. The value is split on
   whitespace and a new process is spawned with the result. Therefore, the
   first argument must be the absolute path to an executable.

   The literal "%repo%" will be replaced with the path of the repository
   being operated on.

   See "moz.build wrapper commands" for more.

moz.build Wrapper Commands
==========================

Some moz.build file info lookups are performed via a separate process. The
process to invoke is defined by the ``hgmo.mozbuildinfowrapper`` option.

The reason for this is security. moz.build files are Python files that must
be executed in a Python interpreter. Python is notoriously difficult (read:
impossible) to sandbox properly. Therefore, we cannot trust that moz.build
files don't contain malicious code which may escape the moz.build execution
context and compromise the Mercurial server. Wrapper commands exist to
allow a more secure execution environment/sandbox to be established so escapes
from the Python moz.build environment can't gain additional permissions.

The program defined by ``hgmo.mozbuildinfowrapper`` is invoked and parameters
are passed to it as JSON via stdin. The stdin pipe is closed once all JSON
has been sent. The JSON properties are:

repo
   Path to repository being operated on.

node
   40 character hex SHA-1 of changeset being queried.

paths
   Array of paths we're interested in information about.

Successful executions will emit JSON on stdout and exit with code 0.
Non-0 exit codes will result in output being logged locally and a generic
message being returned to the user. stderr is logged in all cases.

Wrapper commands typically read arguments, set up a secure execution
environment, then invoke the relevant mozbuild APIs to obtain requested info.

Wrapper commands may invoke ``hg mozbuildinfo --pipemode`` to retrieve
moz.build info. In fact, the wrapper command itself can be defined as this
string. Of course, no security will be provided.
"""

import json
import os
import subprocess

from mercurial.i18n import _
from mercurial.node import short
from mercurial import (
    cmdutil,
    commands,
    encoding,
    error,
    extensions,
    hg,
    revset,
    util,
)
from mercurial.hgweb import (
    webcommands,
    webutil,
)
from mercurial.hgweb.common import HTTP_OK


OUR_DIR = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

import mozautomation.commitparser as commitparser
import mozhg.mozbuildinfo as mozbuildinfo


cmdtable = {}
command = cmdutil.command(cmdtable)


def addmetadata(repo, ctx, d, onlycheap=False):
    """Add changeset metadata for hgweb templates."""
    bugs = list(set(commitparser.parse_bugs(ctx.description())))
    d['bugs'] = []
    for bug in commitparser.parse_bugs(ctx.description()):
        d['bugs'].append({
            'no': str(bug),
            'url': 'https://bugzilla.mozilla.org/show_bug.cgi?id=%s' % bug,
        })

    d['reviewers'] = []
    for reviewer in commitparser.parse_reviewers(ctx.description()):
        d['reviewers'].append({
            'name': reviewer,
            'revset': 'reviewer(%s)' % reviewer,
        })

    d['backsoutnodes'] = []
    backouts = commitparser.parse_backouts(ctx.description())
    if backouts:
        for node in backouts[0]:
            try:
                bctx = repo[node]
                d['backsoutnodes'].append({'node': bctx.hex()})
            except error.LookupError:
                pass

    # Repositories can define which TreeHerder repository they are associated
    # with.
    treeherder = repo.ui.config('mozilla', 'treeherder_repo')
    if treeherder:
        d['treeherderrepourl'] = 'https://treeherder.mozilla.org/#/jobs?repo=%s' % treeherder

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

    # Look for changesets that back out this one.
    #
    # We limit the distance we search for backouts because an exhaustive
    # search could be very intensive. e.g. you load up the root commit
    # on a repository with 200,000 changesets and that commit is never
    # backed out. This finds most backouts because backouts typically happen
    # shortly after a bad commit is introduced.
    thisshort = short(ctx.node())
    count = 0
    searchlimit = repo.ui.configint('hgmo', 'backoutsearchlimit', 100)
    for bctx in repo.set('%ld::', [ctx.rev()]):
        count += 1
        if count >= searchlimit:
            break

        backouts = commitparser.parse_backouts(bctx.description())
        if backouts and thisshort in backouts[0]:
            d['backedoutbynode'] = bctx.hex()
            break


def changesetentry(orig, web, req, tmpl, ctx):
    """Wraps webutil.changesetentry to provide extra metadata."""
    d = orig(web, req, tmpl, ctx)
    addmetadata(web.repo, ctx, d)
    return d


def changelistentry(orig, web, ctx, tmpl):
    d = orig(web, ctx, tmpl)
    addmetadata(web.repo, ctx, d, onlycheap=True)
    return d


def mozbuildinfowebcommand(web, req, tmpl):
    """Web command handler for the "mozbuildinfo" command."""
    repo = web.repo

    # TODO we should be using the templater instead of emitting JSON directly.
    # But this requires not having the JSON formatter from the
    # pushlog-legacy.py extension.

    if not repo.ui.configbool('hgmo', 'mozbuildinfoenabled', False):
        req.respond(HTTP_OK, 'application/json')
        return json.dumps({'error': 'moz.build evaluation is not enabled for this repo'})

    if not repo.ui.config('hgmo', 'mozbuildinfowrapper'):
        req.respond(HTTP_OK, 'application/json')
        return json.dumps({'error': 'moz.build wrapper command not defined; refusing to execute'})

    rev = 'tip'
    if 'node' in req.form:
        rev = req.form['node'][0]

    ctx = repo[rev]
    paths = req.form.get('p', ctx.files())

    pipedata = json.dumps({
        'repo': repo.root,
        'node': ctx.hex(),
        'paths': paths,
    })

    args = repo.ui.config('hgmo', 'mozbuildinfowrapper')
    # Should be verified by extsetup. Double check since any process invocation
    # has security implications.
    assert '"' not in args
    assert "'" not in args
    args = args.split()
    args = [a.replace('%repo%', repo.root) for a in args]

    # We do not use a shell because it is only a vector for pain and possibly
    # security issues.
    # We close file descriptors out of security paranoia.
    # We switch cwd of the process so state from the current directory isn't
    # picked up.
    try:
        p = subprocess.Popen(args,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd='/',
                             shell=False,
                             close_fds=True)
    except OSError as e:
        repo.ui.log('error invoking moz.build info process: %s\n' % e.errno)
        return json.dumps({'error': 'unable to invoke moz.build info process'})

    stdout, stderr = p.communicate(pipedata)

    req.respond(HTTP_OK, 'application/json')

    if p.returncode:
        repo.ui.log('failure obtaining moz.build info: stdout: %s; '
                    'stderr: %s\n' % (stdout, stderr))
        return json.dumps({'error': 'unable to obtain moz.build info'},
                          indent=2)
    elif stderr.strip():
        repo.ui.log('moz.build evaluation output: %s\n' % stderr.strip())

    # Round trip to ensure we have valid JSON.
    try:
        d = json.loads(stdout)
        return json.dumps(d, indent=2, sort_keys=True)
    except Exception:
        return json.dumps({'error': 'invalid JSON returned; report this error'},
                          indent=2)


def infowebcommand(web, req, tmpl):
    """Get information about the specified changeset(s).

    This is a legacy API from before the days of Mercurial's built-in JSON
    API. It is used by unidentified parts of automation. Over time these
    consumers should transition to the modern/native JSON API.
    """
    if 'node' not in req.form:
        return tmpl('error', error={'error': "missing parameter 'node'"})

    csets = []
    for node in req.form['node']:
        ctx = web.repo[node]
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

    return tmpl('info', csets=csets)


def headdivergencewebcommand(web, req, tmpl):
    """Get information about divergence between this repo and a changeset.

    This API was invented to be used by MozReview to obtain information about
    how a repository/head has progressed/diverged since a commit was submitted
    for review.

    It is assumed that this is running on the canonical/mainline repository.
    Changes in other repositories must be rebased onto or merged into
    this repository.
    """
    if 'node' not in req.form:
        return tmpl('error', error={'error': "missing parameter 'node'"})

    repo = web.repo

    paths = set(req.form.get('p', []))
    basectx = repo[req.form['node'][0]]

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

    return tmpl('headdivergence', commitsbehind=commitsbehind,
                filemerges=filemerges, filemergesignored=filemergesignored)


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

        setconfig('pushlog', ['pushlog'])
        setconfig('buglink', ['pushlog-legacy', 'buglink.py'])
        setconfig('pushlog-feed', ['pushlog-legacy', 'pushlog-feed.py'])

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
    if opts['pipemode']:
        data = json.loads(ui.fin.read())

        repo = hg.repository(ui, path=data['repo'])
        ctx = repo[data['node']]
        paths = data['paths']
    else:
        ctx = repo[opts['rev']]

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


def extsetup(ui):
    extensions.wrapfunction(webutil, 'changesetentry', changesetentry)
    extensions.wrapfunction(webutil, 'changelistentry', changelistentry)

    revset.symbols['reviewer'] = revset_reviewer
    revset.safesymbols.add('reviewer')

    entry = extensions.wrapcommand(commands.table, 'serve', servehgmo)
    entry[1].append(('', 'hgmo', False,
                     'Run a server configured like hg.mozilla.org'))

    wrapper = ui.config('hgmo', 'mozbuildinfowrapper')
    if wrapper:
        if '"' in wrapper or "'" in wrapper:
            raise util.Abort('quotes may not appear in hgmo.mozbuildinfowrapper')

    setattr(webcommands, 'mozbuildinfo', mozbuildinfowebcommand)
    webcommands.__all__.append('mozbuildinfo')

    setattr(webcommands, 'info', infowebcommand)
    webcommands.__all__.append('info')

    setattr(webcommands, 'headdivergence', headdivergencewebcommand)
    webcommands.__all__.append('headdivergence')
