# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

def hook(ui, repo, **kwargs):
    if 'bundle2' not in kwargs:
        ui.write('\n')
        ui.write('YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!\n')
        ui.write('newer versions are faster and have numerous bug fixes\n')
        ui.write('upgrade instructions are at the following URL:\n')
        ui.write('https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmozilla/installing.html\n')

    return 0
