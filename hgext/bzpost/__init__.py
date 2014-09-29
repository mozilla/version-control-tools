# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Post changeset URLs to Bugzilla.

This extension will post the URLs of pushed changesets to Bugzilla
automatically.

To use, activate this extension by adding the following to your
hgrc:

    [extensions]
    bzpost = /path/to/version-control-tools/hgext/bzpost

You will also want to define your Bugzilla credentials in your hgrc to
avoid prompting:

    [bugzilla]
    username = foo@example.com
    password = password

After successfully pushing to a known Firefox repository, this extension
will add a comment to the first referenced bug in all pushed changesets
containing the URLs of the pushed changesets.

Limitations
===========

We currently only post comments to integration/non-release repositories.
This is because pushes to release repositories involve updating other
Bugzilla fields. This extension could support these someday - it just
doesn't yet.
"""

import os

from mercurial import demandimport
from mercurial import exchange
from mercurial import extensions
from mercurial.i18n import _

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

# requests doesn't like lazy module loading.
demandimport.disable()
from bugsy import Bugsy
demandimport.enable()
from mozautomation.commitparser import parse_bugs
from mozautomation.repository import (
    BASE_READ_URI,
    BASE_WRITE_URI,
    RELEASE_TREES,
    resolve_trees_to_uris,
    resolve_uri_to_tree,
)
from mozhg.auth import getbugzillaauth

testedwith = '3.0 3.0.1 3.0.2 3.1'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Other%20Applications&component=bzpost'

def wrappedpushbookmark(orig, pushop):
    result = orig(pushop)

    # Don't do anything if error from push.
    if not pushop.ret:
        return result

    remoteurl = pushop.remote.url()
    tree = resolve_uri_to_tree(remoteurl)
    # We don't support release trees (yet) because they have special flags
    # that need to get updated.
    if tree and tree in RELEASE_TREES:
        return result

    tbpltree = None

    if tree:
        baseuri = resolve_trees_to_uris([tree])[0][1]
        assert baseuri

        if tree == 'try':
            tbpltree = 'Try'
    else:
        # This isn't a known Firefox tree. Fall back to resolving URLs by
        # hostname.

        # Only attend Mozilla's server.
        if not remoteurl.startswith(BASE_WRITE_URI):
            return result

        baseuri = remoteurl.replace(BASE_WRITE_URI, BASE_READ_URI).rstrip('/')

    bugsmap = {}
    lastbug = None
    lastnode = None

    for node in pushop.outgoing.missing:
        ctx = pushop.repo[node]

        # Don't do merge commits.
        if len(ctx.parents()) > 1:
            continue

        # Our bug parser is buggy for Gaia bump commit messages.
        if '<release+b2gbumper@mozilla.com>' in ctx.user():
            continue

        bugs = parse_bugs(ctx.description())

        if not bugs:
            continue

        bugsmap.setdefault(bugs[0], []).append(ctx.hex()[0:12])
        lastbug = bugs[0]
        lastnode = ctx.hex()[0:12]

    if not bugsmap:
        return result

    ui = pushop.ui
    bzauth = getbugzillaauth(ui)
    if not bzauth or not bzauth.username or not bzauth.password:
        return result

    bzurl = ui.config('bugzilla', 'url', 'https://bugzilla.mozilla.org/rest')

    bugsy = Bugsy(username=bzauth.username, password=bzauth.password,
            bugzilla_url=bzurl)

    # If this is a try push, we paste the TBPL link for the tip commit, because
    # the per-commit URLs don't have much value.
    # TODO roll this into normal pushing so we get a TBPL link in bugs as well.
    if tbpltree and lastbug:
        tbplurl = 'https://tbpl.mozilla.org/?tree=%s&rev=%s' % (
            tbpltree, lastnode)

        bug = bugsy.get(lastbug)
        comments = bug.get_comments()
        for comment in comments:
            if tbplurl in comment.text:
                return result

        ui.write(_('recording TBPL push in bug %s\n') % lastbug)
        bug.add_comment(tbplurl)
        return result

    for bugnumber, nodes in bugsmap.items():
        bug = bugsy.get(bugnumber)

        comments = bug.get_comments()
        missing_nodes = []

        # When testing whether this changeset URL is referenced in a
        # comment, we only need to test for the node fragment. The
        # important side-effect is that each unique node for a changeset
        # is recorded in the bug.
        for node in nodes:
            if not any(node in comment.text for comment in comments):
                missing_nodes.append(node)

        if not missing_nodes:
            ui.write(_('bug %s already knows about pushed changesets\n') %
                bugnumber)
            continue

        lines = ['%s/rev/%s' % (baseuri, node) for node in missing_nodes]

        comment = '\n'.join(lines)

        ui.write(_('recording push in bug %s\n') % bugnumber)
        bug.add_comment(comment)

    return result

def extsetup(ui):
    extensions.wrapfunction(exchange, '_pushbookmark', wrappedpushbookmark)
