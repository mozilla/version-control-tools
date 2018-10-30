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
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.util import (
    repo_owner,
)

minimumhgversion = '4.6'
testedwith = '4.6 4.7 4.8'


@wireprotov1server.wireprotocommand('mozowner', '', permission='pull')
def moz_owner_command(repo, proto):
    """Obtain the group owner of the repository."""
    return repo_owner(repo)


def _capabilities(orig, *args, **kwargs):
    caps = orig(*args, **kwargs)
    caps.append('moz-owner')
    return caps


class sshv1peer(sshpeer.sshv1peer):
    def mozowner(self):
        self.requirecap('moz-owner', _('moz-owner'))
        return self._call('mozowner')


def exchange_pull_owner(orig, pullop):
    res = orig(pullop)

    if ('moz-owner' in pullop.stepsdone
        or not pullop.remote.capable('moz-owner')):
        return res

    pullop.stepsdone.add('moz-owner')

    group = pullop.remote.mozowner()

    existing = pullop.repo.vfs.tryread('moz-owner')
    if existing != group + '\n':
        pullop.repo.ui.write('updating moz-owner file\n')
        with pullop.repo.vfs('moz-owner', 'wb', atomictemp=True) as fh:
            fh.write(group + '\n')


def extsetup(ui):
    extensions.wrapfunction(wireprotov1server, '_capabilities', _capabilities)
    extensions.wrapfunction(exchange, '_pullobsolete', exchange_pull_owner)

    sshpeer.sshv1peer = sshv1peer
