# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Replicate repository group owner."""

import os

from mercurial.i18n import _
from mercurial import (
    exchange,
    extensions,
    sshpeer,
    wireprotov1server,
)

OUR_DIR = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

from mozhg.util import (
    repo_owner,
)

minimumhgversion = b'4.6'
testedwith = b'4.6 4.7 4.8 4.9 5.0 5.1 5.2 5.3'


@wireprotov1server.wireprotocommand(b'mozowner', b'', permission=b'pull')
def moz_owner_command(repo, proto):
    """Obtain the group owner of the repository."""
    return repo_owner(repo)


def _capabilities(orig, *args, **kwargs):
    caps = orig(*args, **kwargs)
    caps.append(b'moz-owner')
    return caps


class sshv1peer(sshpeer.sshv1peer):
    def mozowner(self):
        self.requirecap(b'moz-owner', _('moz-owner'))
        return self._call(b'mozowner')


def exchange_pull_owner(orig, pullop):
    res = orig(pullop)

    if (b'moz-owner' in pullop.stepsdone
        or not pullop.remote.capable(b'moz-owner')):
        return res

    pullop.stepsdone.add(b'moz-owner')

    group = pullop.remote.mozowner()

    existing = pullop.repo.vfs.tryread(b'moz-owner')
    if existing != group + b'\n':
        pullop.repo.ui.write(b'updating moz-owner file\n')
        with pullop.repo.vfs(b'moz-owner', b'wb', atomictemp=True) as fh:
            fh.write(group + b'\n')


def extsetup(ui):
    extensions.wrapfunction(wireprotov1server, b'_capabilities', _capabilities)
    extensions.wrapfunction(exchange, b'_pullobsolete', exchange_pull_owner)

    sshpeer.sshv1peer = sshv1peer
