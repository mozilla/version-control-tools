# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Replicate repository group owner."""

import grp
import os

from mercurial.i18n import _
from mercurial import (
    exchange,
    extensions,
    sshpeer,
    util,
)

OUR_DIR = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.util import (
    import_module,
    repo_owner,
)

# TRACKING hg46 wireproto -> wireprotov1server
wireproto = import_module('mercurial.wireprotov1server')
if not wireproto:
    wireproto = import_module('mercurial.wireproto')


minimumhgversion = '4.5'
testedwith = '4.5 4.6'


@wireproto.wireprotocommand('mozowner', '')
def moz_owner_command(repo, proto):
    """Obtain the group owner of the repository."""
    return repo_owner(repo)


# TRACKING hg46 wireproto.permissions moved into @wireproto.wireprotocommand
if util.safehasattr(wireproto, 'permissions'):
    wireproto.permissions['mozowner'] = 'pull'
else:
    wireproto.commands['mozowner'].permission = 'pull'


def _capabilities(orig, *args, **kwargs):
    caps = orig(*args, **kwargs)
    caps.append('moz-owner')
    return caps


# TRACKING hg46
if util.safehasattr(sshpeer, 'sshv1peer'):
    sshpeerbase = sshpeer.sshv1peer
else:
    sshpeerbase = sshpeer.sshpeer

class sshv1peer(sshpeerbase):
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
    extensions.wrapfunction(wireproto, '_capabilities', _capabilities)
    extensions.wrapfunction(exchange, '_pullobsolete', exchange_pull_owner)

    # TRACKING hg46
    if util.safehasattr(sshpeer, 'sshv1peer'):
        sshpeer.sshv1peer = sshv1peer
    else:
        sshpeer.sshpeer = sshv1peer
        sshpeer.instance = sshv1peer
