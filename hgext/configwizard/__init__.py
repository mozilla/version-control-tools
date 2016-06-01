# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Manage Mercurial configuration in a Mozilla-tailored way."""

import difflib
import io
import os
import uuid

from mercurial import (
    cmdutil,
    error,
    scmutil,
    util,
)
from mercurial.i18n import _

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from configobj import ConfigObj

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

MISSING_USERNAME = '''
You don't have a username defined in your Mercurial config file. In order
to author commits, you'll need to define a name and e-mail address.

This data will be publicly available when you send commits/patches to others.
If you aren't comfortable giving us your full name, pseudonames are
acceptable.

(Relevant config option: ui.username)
'''.lstrip()

BAD_DIFF_SETTINGS = '''
Mercurial is not configured to produce diffs in a more readable format.

Would you like to change this (Yn)? $$ &Yes $$ &No
'''.strip()

testedwith = '3.5 3.6 3.7 3.8'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=General'

cmdtable = {}
command = cmdutil.command(cmdtable)

wizardsteps = {
    'hgversion',
    'username',
    'diff',
    'color',
    'configchange',
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

    configpaths = [p for p in scmutil.userrcpath() if os.path.exists(p)]
    path = configpaths[0] if configpaths else scmutil.userrcpath()[0]
    cw = configobjwrapper(path)

    if 'hgversion' in runsteps:
        if _checkhgversion(ui, hgversion):
            return 1

    if 'username' in runsteps:
        _checkusername(ui, cw)

    if 'diff' in runsteps:
        _checkdiffsettings(ui, cw)

    if 'color' in runsteps:
        _promptnativeextension(ui, cw, 'color', 'Enable color output to your terminal')

    if 'configchange' in runsteps:
        return _handleconfigchange(ui, cw)

    return 0


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


def uipromptchoice(ui, msg):
    lines = msg.splitlines(True)
    ui.write(''.join(lines[0:-1]))
    return ui.promptchoice(lines[-1])


def _checkusername(ui, cw):
    if ui.config('ui', 'username'):
        return

    ui.write(MISSING_USERNAME)

    name, email = None, None

    name = ui.prompt('What is your name?', '')
    if name:
        email = ui.prompt('What is your e-mail address?', '')

    if name and email:
        username = '%s <%s>' % (name, email)
        if 'ui' not in cw.c:
            cw.c['ui'] = {}
        cw.c['ui']['username'] = username.strip()

        ui.write('setting ui.username=%s\n\n' % username)
    else:
        ui.warn('Unable to set username; You will be unable to author '
                'commits\n\n')


def _checkdiffsettings(ui, cw):
    git = ui.configbool('diff', 'git')
    showfunc = ui.configbool('diff', 'showfunc')

    if git and showfunc:
        return

    if not uipromptchoice(ui, BAD_DIFF_SETTINGS):
        if 'diff' not in cw.c:
            cw.c['diff'] = {}

        cw.c['diff']['git'] = 'true'
        cw.c['diff']['showfunc'] = 'true'


def _promptnativeextension(ui, cw, ext, msg):
    if ui.hasconfig('extensions', ext):
        return

    if not ui.promptchoice('%s (Yn) $$ &Yes $$ &No' % msg):
        if 'extensions' not in cw.c:
            cw.c['extensions'] = {}

        cw.c['extensions'][ext] = ''


def _handleconfigchange(ui, cw):
    # Obtain the old and new content so we can show a diff.
    newbuf = io.BytesIO()
    cw.write(newbuf)
    newbuf.seek(0)
    newlines = [l.rstrip() for l in newbuf.readlines()]
    oldlines = []
    if os.path.exists(cw.path):
        with open(cw.path, 'rb') as fh:
            oldlines = [l.rstrip() for l in fh.readlines()]

    diff = list(difflib.unified_diff(oldlines, newlines,
                                     'hgrc.old', 'hgrc.new',
                                     lineterm=''))

    if len(diff):
        ui.write('Your config file needs updating.\n')
        if not ui.promptchoice('Would you like to see a diff of the changes first (Yn)? $$ &Yes $$ &No'):
            for line in diff:
                ui.write('%s\n' % line)
            ui.write('\n')

        if not ui.promptchoice('Write changes to hgrc file (Yn)? $$ &Yes $$ &No'):
            with open(cw.path, 'wb') as fh:
                fh.write(newbuf.getvalue())
        else:
            ui.write('config changes not written; we would have written the following:\n')
            ui.write(newbuf.getvalue())
            return 1


class configobjwrapper(object):
    """Manipulate config files with ConfigObj.

    Mercurial doesn't support writing config files. ConfigObj does. ConfigObj
    also supports preserving comments in config files, which is user friendly.

    This class provides a mechanism to load and write config files with
    ConfigObj.
    """
    def __init__(self, path):
        self.path = path
        self._random = str(uuid.uuid4())

        lines = []

        if os.path.exists(path):
            with open(path, 'rb') as fh:
                for line in fh:
                    # Mercurial has special syntax to include other files.
                    # ConfigObj doesn't recognize it. Normalize on read and
                    # restore on write to preserve it.
                    if line.startswith('%include'):
                        line = '#%s %s' % (self._random, line)

                    if line.startswith(';'):
                        raise error.Abort('semicolon (;) comments in config '
                                          'files not supported',
                                          hint='use # for comments')

                    lines.append(line)

        self.c = ConfigObj(infile=lines, encoding='utf-8',
                           write_empty_values=True, list_values=False)

    def write(self, fh):
        lines = self.c.write()
        for line in lines:
            if line.startswith('#%s ' % self._random):
                line = line[2 + len(self._random):]

            fh.write('%s\n' % line)

