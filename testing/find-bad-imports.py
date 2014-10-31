# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""This extension is used during testing to find bad imports.

It introduces a command that is used to test if bad imports are detected.
The extension is presumably loaded with other extensions that trigger bad
imports.

Once the test harness runs on Windows, we can probably remove this.
See bug 1096499.
"""

import sys

from mercurial import (
    cmdutil,
    commands,
)

BAD_MODULES = set([
    'json',
])

cmdtable = {}
command = cmdutil.command(cmdtable)

commands.norepo += ' findbadimports'

@command('findbadimports', [], ('hg findbadimports'))
def findbadimports(ui):
    have_bad = False
    for m in sorted(BAD_MODULES):
        if m in sys.modules:
            ui.write('bad import: %s\n' % m)
            have_bad = True

    return have_bad
