# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Review Board server extension

This extensions adds a custom wire protocol command to the server to receive
new review requests.

This extension requires configuration before it can work.

The [reviewboard] section in the hgrc must have the following:

* url - the string URL of the Review Board server to talk to.
* repoid - the integer repository ID of this repository in Review Board.

url is commonly defined in the global hgrc whereas repoid is repository
local.
"""

import os
import sys

from mercurial import demandimport
from mercurial import extensions
from mercurial import util
from mercurial import wireproto
from mercurial.i18n import _

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
REPO_ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))

demandimport.disable()
try:
    import hgrb.shared
except ImportError:
    sys.path.insert(0, os.path.join(REPO_ROOT, 'pylib', 'reviewboardmods'))
    sys.path.insert(0, OUR_DIR)
    import hgrb.shared
demandimport.enable()

testedwith = '3.0.1'

def capabilities(orig, repo, proto):
    """Wraps wireproto._capabilities to advertise reviewboard support."""
    caps = orig(repo, proto)

    if repo.ui.configint('reviewboard', 'repoid', None):
        caps.append('reviewboard')

    return caps

def changegrouphook(ui, repo, source, url, **kwargs):
    # We send output to *every* client that the reviewboard client
    # extension is required. The reviewboard client extension will
    # filter this output.
    repo.ui.write(
        _('REVIEWBOARD: You need to have the reviewboard client extension '
          'installed in order to perform code reviews.\n'))
    repo.ui.write(
        _('REVIEWBOARD: See https://hg.mozilla.org/hgcustom/version-control-tools/file/tip/hgext/reviewboard/README.rst\n'))

def extsetup(ui):
    extensions.wrapfunction(wireproto, '_capabilities', capabilities)

def reposetup(ui, repo):
    if not repo.local():
        return

    if not ui.config('reviewboard', 'url', None):
        raise util.Abort(_('Please set reviewboard.url to the URL of the '
            'Review Board instance to talk to.'))

    if not ui.configint('reviewboard', 'repoid', None):
        raise util.Abort(_('Please set reviewboard.repoid to the numeric ID '
            'of the repository this repo is associated with.'))

    if ui.configbool('phases', 'publish', True):
        raise util.Abort(_('reviewboard server extension is only compatible '
            'with non-publishing repositories.'))

    ui.setconfig('hooks', 'changegroup.reviewboard', changegrouphook)

