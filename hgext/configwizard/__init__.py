# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Manage Mercurial configuration in a Mozilla-tailored way."""

import os

from mercurial import (
    cmdutil,
    error,
    util,
)
from mercurial.i18n import _

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

INITIAL_MESSAGE = '''
This wizard will guide you through configuring Mercurial for an optimal
experience contributing to Mozilla projects.

The wizard makes no changes without your permission.

To begin, press the enter/return key.
'''.lstrip()

MINIMUM_SUPPORTED_VERSION = (3, 5, 0)

OLDEST_NON_LEGACY_VERSION = (3, 7, 3)

VERSION_TOO_OLD = '''
Your version of Mercurial is too old to run `hg configwizard`.

Mozilla's Mercurial support policy is to support at most the past
1 year of Mercurial releases (or 4 major Mercurial releases).
'''.lstrip()

LEGACY_MERCURIAL_MESSAGE = '''
You are running an out of date Mercurial client (%s).

For a faster and better Mercurial experience, we HIGHLY recommend you
upgrade.

Legacy versions of Mercurial have known security vulnerabilities. Failure
to upgrade may leave you exposed. You are highly encouraged to upgrade in
case you aren't running a patched version.
'''.lstrip()


testedwith = '3.5 3.6 3.7 3.8'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=General'

cmdtable = {}
command = cmdutil.command(cmdtable)

wizardsteps = {
    'hgversion',
}

@command('configwizard', [
    ('s', 'statedir', '', _('directory to store state')),
    ], _('hg configwizard'), optionalrepo=True)
def configwizard(ui, repo, statedir=None, **opts):
    """Ensure your Mercurial configuration is up to date."""
    runsteps = set(wizardsteps)
    if ui.hasconfig('configwizard', 'steps'):
        runsteps = set(ui.configlist('configwizard', 'steps'))

    hgversion = util.versiontuple(n=3)

    if hgversion < MINIMUM_SUPPORTED_VERSION:
        ui.warn(VERSION_TOO_OLD)
        raise error.Abort('upgrade Mercurial then run again')

    uiprompt(ui, INITIAL_MESSAGE, default='<RETURN>')

    if 'hgversion' in runsteps:
        if _checkhgversion(ui, hgversion):
            return 1


def _checkhgversion(ui, hgversion):
    if hgversion >= OLDEST_NON_LEGACY_VERSION:
        return

    ui.warn(LEGACY_MERCURIAL_MESSAGE % util.version())
    ui.warn('\n')

    if os.name == 'nt':
        ui.warn('Please upgrade to the latest MozillaBuild to upgrade '
                'your Mercurial install.\n\n')
    else:
        ui.warn('Please run `mach bootstrap` to upgrade your Mercurial '
                'install.\n\n')

    if ui.promptchoice('Would you like to continue using an old Mercurial version (Yn)? $$ &Yes $$ &No'):
        return 1


def uiprompt(ui, msg, default=None):
    """Wrapper for ui.prompt() that only renders the last line of text as prompt.

    This prevents entire prompt text from rendering as a special color which
    may be hard to read.
    """
    lines = msg.splitlines(True)
    ui.write(''.join(lines[0:-1]))
    return ui.prompt(lines[-1], default=default)
