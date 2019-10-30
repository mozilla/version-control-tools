# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import re

from mercurial.node import short
from mercurial import (
    encoding,
)

RE_PROPER_AUTHOR = re.compile(br'^[^<]+\s\<[^<>]+@[^<>]+\>$')

def hook(ui, repo, node, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    havebad = False

    for rev in xrange(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        user = ctx.user()

        # These are frequently used in automation. Ignore them for now.
        if user in (b'ffxbld', b'tbirdbld', b'seabld'):
            continue

        if not RE_PROPER_AUTHOR.match(user):
            ui.write(b'malformed user field in changeset %s: %s\n' % (
                short(ctx.node()), user))
            havebad = True

    if not havebad:
        return 0

    ui.write(
        b'user fields must be of the format "author <email>"\n'
        b'e.g. "Mozilla Contributor <someone@example.com>"\n'
        b'set "ui.username" in your hgrc to a well-formed value\n'
        b'\n'
        b'"graft" can be used to rewrite multiple changesets to have a different user value\n'
        b'use the "--currentuser" or "--user" arguments to "graft" to specify an explicit user\n'
        b'\n'
        b'`hg up %(parent)s && hg graft --currentuser -r %(first)s::`\n'
        b'will rewrite all pushed changesets and their descendants to the current user value\n'
        b'\n'
        b"`hg up %(parent)s && hg graft --user 'Some User <someone@example.com>' -r %(first)s::%(tip)s`\n"
        b'will rewrite just the pushed changesets to an explicit username\n'
        % {
            b'parent': short(repo[node].p1().node()),
            b'first': short(repo[node].node()),
            b'tip': short(repo[b'tip'].node()),
        }
    )

    # Make non-fatal on l10n repos for now because their tools are known to not
    # use proper values.
    if b'l10n' in repo.path:
        havebad = False

    return 1 if havebad else 0
