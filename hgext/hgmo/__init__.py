# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Provide enhancements to hg.mozilla.org's web interface."""

import os

import mercurial.encoding as encoding
import mercurial.errors as errors
import mercurial.extensions as extensions
import mercurial.hgweb.webutil as webutil
import mercurial.revset as revset


OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

import mozautomation.commitparser as commitparser


def addmetadata(repo, ctx, d):
    """Add changeset metadata for hgweb templates."""
    bugs = list(commitparser.parse_bugs(ctx.description()))
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

    # Obtain the Gecko/app version/milestone.
    #
    # We could probably only do this if the repo is a known app repo (by
    # looking at the initial changeset). But, path based lookup is relatively
    # fast, so just do it.
    try:
        fctx = repo.filectx('config/milestone.txt', changeid=ctx.node())
        lines = fctx.data().splitlines()
        lines = [l for l in lines if not l.startswith('#') and l.strip()]

        if lines:
            d['milestone'] = lines[0].strip()
    except LookupError:
        pass

    d['backsoutnodes'] = []
    backouts = commitparser.parse_backouts(ctx.description())
    if backouts:
        for node in backouts[0]:
            try:
                bctx = repo[node]
                d['backsoutnodes'].append({'node': bctx.hex()})
            except LookupError:
                pass


def changesetentry(orig, web, req, tmpl, ctx):
    """Wraps webutil.changesetentry to provide extra metadata."""
    d = orig(web, req, tmpl, ctx)
    addmetadata(web.repo, ctx, d)
    return d


def changelistentry(orig, web, ctx, tmpl):
    d = orig(web, ctx, tmpl)
    addmetadata(web.repo, ctx, d)
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


def extsetup(ui):
    extensions.wrapfunction(webutil, 'changesetentry', changesetentry)
    extensions.wrapfunction(webutil, 'changelistentry', changelistentry)

    revset.symbols['reviewer'] = revset_reviewer
    revset.safesymbols.add('reviewer')
