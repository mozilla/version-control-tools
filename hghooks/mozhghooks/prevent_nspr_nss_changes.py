# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os

from mercurial.node import short

def hook(ui, repo, node, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    # Leave uplifts alone.
    if b'a=release' in repo[b'tip'].description().lower():
        return 0

    nspr_nodes = []
    nss_nodes = []

    for rev in repo.changelog.revs(repo[node].rev()):
        ctx = repo[rev]

        # Skip merge changesets.
        if len(ctx.parents()) > 1:
            continue

        if any(f.startswith(b'nsprpub/') for f in ctx.files()):
            if b'UPGRADE_NSPR_RELEASE' not in ctx.description():
                nspr_nodes.append(short(ctx.node()))

        if any(f.startswith(b'security/nss/') for f in ctx.files()):
            if b'UPGRADE_NSS_RELEASE' not in ctx.description():
                nss_nodes.append(short(ctx.node()))

    res = 0

    if nspr_nodes or nss_nodes:
        if nspr_nodes:
            ui.write(b'(%d changesets contain changes to protected nsprpub/ '
                     b'directory: %s)\n' % (len(nspr_nodes), b', '.join(nspr_nodes)))
            res = 1

        if nss_nodes:
            ui.write(b'(%d changesets contain changes to protected security/nss/ '
                     b'directory: %s)\n' % (len(nss_nodes), b', '.join(nss_nodes)))
            res = 1

        if res:
            header = b'*' * 72
            ui.write(b'%s\n' % header)
            ui.write(b'You do not have permissions to modify files under '
                     b'nsprpub/ or security/nss/\n')
            ui.write(b'\n')
            ui.write(b'These directories are kept in sync with the canonical '
                     b'upstream repositories at\n'
                     b'https://hg.mozilla.org/projects/nspr and '
                     b'https://hg.mozilla.org/projects/nss\n')
            ui.write(b'\n')
            ui.write(b'Please contact the NSPR/NSS maintainers at nss-dev@mozilla.org or on IRC\n'
                     b'channel #nss to request that your changes are merged, released and uplifted.\n')
            ui.write(b'%s\n' % header)

    return res
