# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""This hook prevents additional roots from being introduced to a repo."""

from mercurial.node import (
    bin,
    nullid,
    short,
)

from mozhg.util import (
    identify_repo,
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

    info = identify_repo(repo)

    # Only apply to hosted repos since we don't want hook to affect one-off
    # repos on disk.
    if not info['hosted']:
        return 0

    # Don't apply hook to user repos, since user repos are the wild west.
    if info['user_repo']:
        return 0

    newroots = set()

    for rev in range(repo[node].rev(), len(repo)):
        ctx = repo[rev]
        if rev == 0:
            continue

        if ctx.p1().node() == nullid:
            newroots.add(ctx.node())

    if not newroots:
        return 0

    # Allow the config to declare allowed new roots.
    #
    # Lists of allowed roots are indexed by the initial rev 0 changeset
    # of the repo. This means different logical repositories have
    # different sets of allowed roots. This also means the allowed roots
    # for a logical repository only has to be declared once (presumably
    # in the global hgrc) for it to work on all clones of that repo.
    #
    # We don't have a global list of allowed roots shared across all repos
    # because it would be possible to push any root in that global set to
    # any repo, completely undermining the hook.
    #
    # We also don't support magic syntax in commit messages to allow new
    # roots because we don't trust users to not abuse this.

    allowedroots = ui.configlist('allowedroots', repo[0].hex())
    allowedroots = set(map(bin, allowedroots))

    badroots = newroots - allowedroots
    goodroots = newroots & allowedroots

    for root in sorted(goodroots):
        ui.write('(allowing new root %s because it is in the whitelist)\n' %
                 short(root))

    if not badroots:
        return 0

    ui.write(MESSAGE % ', '.join(sorted(map(short, badroots))))
    return 1
