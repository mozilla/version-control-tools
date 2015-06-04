# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Provide enhancements to hg.mozilla.org's web interface."""

import os

import mercurial.extensions as extensions
import mercurial.hgweb.webutil as webutil

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

    d['reviewers'] = list(commitparser.parse_reviewers(ctx.description()))


def changesetentry(orig, web, req, tmpl, ctx):
    """Wraps webutil.changesetentry to provide extra metadata."""
    d = orig(web, req, tmpl, ctx)
    addmetadata(web.repo, ctx, d)
    return d


def changelistentry(orig, web, ctx, tmpl):
    d = orig(web, ctx, tmpl)
    addmetadata(web.repo, ctx, d)
    return d


def extsetup(ui):
    extensions.wrapfunction(webutil, 'changesetentry', changesetentry)
    extensions.wrapfunction(webutil, 'changelistentry', changelistentry)
