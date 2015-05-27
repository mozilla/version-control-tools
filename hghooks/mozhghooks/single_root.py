# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""This hook prevents additional roots from being introduced to a repo."""

from mercurial.node import (
    nullid,
    short,
)

MESSAGE = '''
*** pushing unrelated repository ***

Changeset %s introduces a new root changeset into this repository. This
almost certainly means you accidentally force pushed to the wrong
repository and/or URL.

Your push is being rejected because this is almost certainly not what you
intended.
'''.lstrip()

def hook(ui, repo, hooktype, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    for rev in range(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        if rev == 0:
            continue

        if ctx.p1().node() == nullid:
            ui.write(MESSAGE % short(ctx.hex()))
            return 1

    return 0
