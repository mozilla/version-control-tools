# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy extension to change the URLs of Mozilla repositories to local URLs.

A number of extensions change behavior when interacting with Mozilla
repositories. Answering "is a Mozilla repository" typically works by
examining the repository URL.

Enabling this extension causes local repositories in the test environment
to answer true to "is a Mozilla repository."
"""

import os
import sys

from mercurial import (
    registrar,
    util,
)

try:
    from mozautomation import repository
except ImportError:
    root = os.path.join(os.path.dirname(__file__), '..')
    sys.path.insert(0, os.path.normpath(os.path.join(root, 'pylib', 'mozautomation')))

    from mozautomation import repository


# TRACKING hg43 Mercurial 4.3 introduced the config registrar. 4.4 requires
# config items to be registered to avoid a devel warning.
if util.safehasattr(registrar, 'configitem'):
    configtable = {}
    configitem = registrar.configitem(configtable)

    configitem('localmozrepo', 'readuri', default=None)
    configitem('localmozrepo', 'writeuri', default=None)


def extsetup(ui):
    read_uri = ui.config('localmozrepo', 'readuri')
    write_uri = ui.config('localmozrepo', 'writeuri')

    if read_uri:
        repository.BASE_READ_URI = read_uri
    if write_uri:
        repository.BASE_WRITE_URI = write_uri
