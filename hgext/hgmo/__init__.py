# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Provide enhancements to hg.mozilla.org's web interface."""

import json
import os

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
)
from mercurial.hgweb import webutil


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
        setconfig('hgwebjson', ['pushlog-legacy', 'hgwebjson.py'])

        # Since new extensions may have been flagged for loading, we need
        # to obtain a new repo instance to a) trigger loading of these
        # extensions b) force extensions' reposetup function to run.
        repo = hg.repository(ui, repo.root)

    return orig(ui, repo, *args, **kwargs)


@command('mozbuildinfo', [
    ('r', 'rev', '.', _('revision to query'), _('REV')),
    ], _('show files info from moz.build files'))
def mozbuildinfocommand(ui, repo, *paths, **opts):
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
