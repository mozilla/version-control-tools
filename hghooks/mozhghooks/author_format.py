# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import re

from mercurial.node import short
from mercurial import (
    encoding,
)

RE_PROPER_AUTHOR = re.compile('^[^<]+\s\<[^<>]+@[^<>]+\>$')

def hook(ui, repo, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    havebad = False

    for rev in xrange(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        user = ctx.user()

        if not RE_PROPER_AUTHOR.match(user):
            ui.write('malformed user field in changeset %s: %s\n' % (
                short(ctx.node()), user))
            havebad = True

    if not havebad:
        return 0

    ui.write(
        'user fields must be of the format "author <email>"\n'
        'e.g. "Mozilla Contributor <someone@example.com>"\n'
        'set "ui.username" in your hgrc to a well-formed value\n'
        '\n'
        '"graft" can be used to rewrite multiple changesets to have a different user value\n'
        'use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user\n'
        '\n'
        '`hg up {parent} && hg graft --currentuser -r {first}::`\n'
        'will rewrite all pushed changesets and their descendants to the current user value\n'
        '\n'
        "`hg up {parent} && hg graft --user 'Some User <someone@example.com>' -r {first}::{tip}`\n"
        'will rewrite just the pushed changesets to an explicit username\n'
        .format(
            parent=short(repo[node].p1().node()),
            first=short(repo[node].node()),
            tip=short(repo['tip'].node())
        ))

    return 1 if havebad else 0
