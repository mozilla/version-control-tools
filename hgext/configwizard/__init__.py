# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Manage Mercurial configuration in a Mozilla-tailored way."""

import difflib
import io
import os
import stat
import subprocess
import sys
import uuid

from mercurial import (
    cmdutil,
    demandimport,
    error,
    ui as uimod,
    util,
)
from mercurial.i18n import _

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from configobj import ConfigObj


HOST_FINGERPRINTS = {
    'bitbucket.org': '3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa',
    'bugzilla.mozilla.org': '7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17',
    'hg.mozilla.org': '73:7f:ef:ab:68:0f:49:3f:88:91:f0:b7:06:69:fd:8f:f2:55:c9:56',
}

MODERN_FINGERPRINTS = {
    'bitbucket.org': 'sha256:4e:65:3e:76:0f:81:59:85:5b:50:06:0c:c2:4d:3c:56:53:8b:83:3e:9b:fa:55:26:98:9a:ca:e2:25:03:92:47',
    'bugzilla.mozilla.org': 'sha256:95:BA:0F:F2:C4:28:75:9D:B5:DB:4A:50:5F:29:46:A3:A9:4E:1B:56:A5:AE:10:50:C3:DD:3A:AC:73:BF:4A:D9',
    'hg.mozilla.org': 'sha256:8e:ad:f7:6a:eb:44:06:15:ed:f3:e4:69:a6:64:60:37:2d:ff:98:88:37:bf:d7:b8:40:84:01:48:9c:26:ce:d9',
}

INITIAL_MESSAGE = '''
This wizard will guide you through configuring Mercurial for an optimal
experience contributing to Mozilla projects.

The wizard makes no changes without your permission.

To begin, press the enter/return key.
'''.lstrip()

MINIMUM_SUPPORTED_VERSION = (3, 5, 0)

# Upgrade Mercurial older than this.
# This should match MODERN_MERCURIAL_VERSION from
# mozilla-central/python/mozboot/mozboot/base.py
OLDEST_NON_LEGACY_VERSION = (4, 2, 3)

VERSION_TOO_OLD = '''
Your version of Mercurial (%d.%d) is too old to run `hg configwizard`.

Mozilla's Mercurial support policy is to support at most the past
1 year of Mercurial releases (or 4 major Mercurial releases).

Please upgrade to Mercurial %d.%d or newer and try again.

See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
for Mozilla-tailored instructions for install Mercurial.
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

MISSING_IRCNICK = '''
You don't have a Mozilla IRC nickname defined in your Mercurial config file.
You will need to add your nick in order to push commits to MozReview.

(Relevant config option: mozilla.ircnick)
'''

BAD_DIFF_SETTINGS = '''
Mercurial is not configured to produce diffs in a more readable format.

Would you like to change this (Yn)? $$ &Yes $$ &No
'''.strip()

PAGER_INFO = '''
The "pager" extension transparently redirects command output to a pager
program (like "less") so command output can be more easily consumed
(e.g. output longer than the terminal can be scrolled).

Please select one of the following for configuring pager:

  1. Enable pager and configure with recommended settings (preferred)
  2. Enable pager with default configuration
  3. Don't enable pager

Which option would you like? $$ &1 $$ &2 $$ &3
'''.strip()

CURSES_INFO = '''
Mercurial can provide richer terminal interactions for some operations
by using the popular "curses" library.

Would you like to enable "curses" interfaces (Yn)? $$ &Yes $$ &No
'''.strip()

WATCHMAN_NOT_FOUND = '''
The "watchman" filesystem watching tool could not be found or isn't
working.

Mercurial can leverage "watchman" to make many operations
(like `hg status` and `hg diff`) much faster. Mozilla *highly*
recommends installing "watchman" when working with the Firefox
repository.

Please see https://facebook.github.io/watchman/docs/install.html
for instructions on installing watchman. Please ensure `watchman`
is available on PATH (you should be able to run `watchman` from
your shell).
'''.lstrip()

FSMONITOR_INFO = '''
The fsmonitor extension integrates the watchman filesystem watching tool
with Mercurial. Commands like `hg status`, `hg diff`, and `hg commit`
(which need to examine filesystem state) can query watchman to obtain
this state, allowing these commands to complete much quicker.

When installed, the fsmonitor extension will automatically launch a
background watchman daemon for accessed Mercurial repositories. It
should "just work."

Would you like to enable fsmonitor (Yn)? $$ &Yes $$ &No
'''.strip()

FSMONITOR_NOT_AVAILABLE = '''
Newer versions of Mercurial have built-in support for integrating with
filesystem watching services to make common operations faster.

This integration is STRONGLY RECOMMENDED when using the Firefox
repository.

Please upgrade to Mercurial 3.8+ so this feature is available.
'''.lstrip()

WIP_INFO = '''
It is common to want a quick view of changesets that are in progress.

The ``hg wip`` command provides such a view.

Example Usage:

  $ hg wip
  @  5887 armenzg tip @ Bug 1313661 - Bump pushlog_client to 0.6.0. r=me
  : o  5885 glob mozreview: Improve the error message when pushing to a submitted/discarded review request (bug 1240725) r?smacleod
  : o  5884 glob hgext: Support line breaks in hgrb error messages (bug 1240725) r?gps
  :/
  o  5883 mars mozreview: add py.test and demonstration tests to mozreview (bug 1312875) r=smacleod
  : o  5881 glob autoland: log mercurial commands to autoland.log (bug 1313300) r?smacleod
  :/
  o  5250 gps ansible/docker-hg-web: set USER variable in httpd process
  |
  ~

(Not shown are the colors that help denote the state each changeset
is in.)

(Relevant config options: alias.wip, revsetalias.wip, templates.wip)

Would you like to install the `hg wip` alias (Yn)? $$ &Yes $$ &No
'''.lstrip()

FIREFOXTREE_INFO = '''
The firefoxtree extension makes interacting with the multiple Firefox
repositories easier:

* Aliases for common trees are pre-defined. e.g. `hg pull central`
* Pulling from known Firefox trees will create "remote refs" appearing as
  tags. e.g. pulling from fx-team will produce a "fx-team" tag.
* The `hg fxheads` command will list the heads of all pulled Firefox repos
  for easy reference.
* `hg push` will limit itself to pushing a single head when pushing to
  Firefox repos.
* A pre-push hook will prevent you from pushing multiple heads to known
  Firefox repos. This acts quicker than a server-side hook.

The firefoxtree extension is *strongly* recommended if you:

a) aggregate multiple Firefox repositories into a single local repo
b) perform head/bookmark-based development (as opposed to mq)

(Relevant config option: extensions.firefoxtree)

Would you like to activate firefoxtree (Yn)? $$ &Yes $$ &No
'''.strip()

CODEREVIEW_INFO = '''
Commits to Mozilla projects are typically sent to MozReview. This is the
preferred code review tool at Mozilla.

Some still practice a legacy code review workflow that uploads patches
to Bugzilla.

1. MozReview only (preferred)
2. Both MozReview and Bugzilla
3. Bugzilla only

Which code review tools will you be submitting code to? $$ &1 $$ &2 $$ &3
'''.strip()

MISSING_BUGZILLA_CREDENTIALS = '''
You do not have a Bugzilla API Key defined in your Mercurial config.

In order to communicate with Bugzilla and services (like MozReview) that
use Bugzilla for authentication, you'll need to supply an API Key.

The Bugzilla API Key is optional. However, if you don't supply one,
certain features may not work and/or you'll be prompted for one.

You should only need to configure a Bugzilla API Key once.
'''.lstrip()

BUGZILLA_API_KEY_INSTRUCTIONS = '''
Bugzilla API Keys can only be obtained through the Bugzilla web interface.

Please perform the following steps:

  1) Open https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey
  2) Generate a new API Key
  3) Copy the generated key and paste it here
'''.lstrip()

LEGACY_BUGZILLA_CREDENTIALS_DETECTED = '''
Your existing Mercurial config uses a legacy method for defining Bugzilla
credentials. Bugzilla API Keys are the most secure and preferred method
for defining Bugzilla credentials. Bugzilla API Keys are also required
if you have enabled 2 Factor Authentication in Bugzilla.

For security reasons, the legacy credentials are being removed from the
config.
'''.lstrip()

PUSHTOTRY_INFO = '''
The push-to-try extension generates a temporary commit with a given
try syntax and pushes it to the try server. The extension is intended
to be used in concert with other tools generating try syntax so that
they can push to try without depending on mq or other workarounds.

(Relevant config option: extensions.push-to-try)

Would you like to activate push-to-try (Yn)? $$ &Yes $$ &No
'''.strip()

MULTIPLE_VCT = '''
*** WARNING ***

Multiple version-control-tools repositories are referenced in your
Mercurial config. Extensions and other code within the
version-control-tools repository could run with inconsistent results.

Please manually edit the following file to reference a single
version-control-tools repository:

    %s

'''.lstrip()

FILE_PERMISSIONS_WARNING = '''
Your hgrc file is currently readable by others.

Sensitive information such as your Bugzilla credentials could be
stolen if others have access to this file/machine.

Would you like to fix the file permissions (Yn) $$ &Yes $$ &No
'''.strip()


testedwith = '3.9 4.0 4.1 4.2 4.3'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20configwizard'

cmdtable = {}

# We want the extension to load on ancient versions of Mercurial.
# cmdutil.command was introduced in 1.9.
# registrar.command was introduced in 4.3 as a replacement for cmdutil.command.
# The registrar module itself was introduced around Mercurial 4.0.
try:
    from mercurial import registrar
    command = registrar.command(cmdtable)
except (ImportError, AttributeError):
    try:
        command = cmdutil.command(cmdtable)
    except AttributeError:
        command = None


wizardsteps = set([
    'hgversion',
    'username',
    'diff',
    'color',
    'pager',
    'curses',
    'historyediting',
    'fsmonitor',
    'blackbox',
    'security',
    'firefoxtree',
    'wip',
    'codereview',
    'pushtotry',
    'multiplevct',
    'configchange',
    'permissions',
])


def configwizard(ui, repo, statedir=None, **opts):
    """Ensure your Mercurial configuration is up to date."""
    runsteps = set(wizardsteps)

    # Mercurial <1.7 had a bug where monkeypatching ui.__class__
    # during uisetup() doesn't work. So we do our own ui.hasconfig()
    # here. Other uses of ui.hasconfig() are allowed, as they will
    # have a properly monkeypatched ui.__class__.
    if 'steps' in ui._data(False)._data.get('configwizard', {}):
        runsteps = set(ui.configlist('configwizard', 'steps'))

    hgversion = util.versiontuple(n=3)

    if hgversion < MINIMUM_SUPPORTED_VERSION:
        ui.warn(VERSION_TOO_OLD % (
            hgversion[0], hgversion[1],
            MINIMUM_SUPPORTED_VERSION[0], MINIMUM_SUPPORTED_VERSION[1],
        ))
        raise error.Abort('upgrade Mercurial then run again')

    uiprompt(ui, INITIAL_MESSAGE, default='<RETURN>')

    with demandimport.deactivated():
        # Mercurial 4.2 moved function from scmutil to rcutil.
        try:
            from mercurial.rcutil import userrcpath
        except ImportError:
            from mercurial.scmutil import userrcpath

    configpaths = [p for p in userrcpath() if os.path.exists(p)]
    path = configpaths[0] if configpaths else userrcpath()[0]
    cw = configobjwrapper(path)

    if 'hgversion' in runsteps:
        if _checkhgversion(ui, hgversion):
            return 1

    if 'username' in runsteps:
        _checkusername(ui, cw)

    if 'diff' in runsteps:
        _checkdiffsettings(ui, cw)

    if 'color' in runsteps:
        _checkcolor(ui, cw, hgversion)

    if 'pager' in runsteps:
        _checkpager(ui, cw, hgversion)

    if 'curses' in runsteps:
        _checkcurses(ui, cw)

    if 'historyediting' in runsteps:
        _checkhistoryediting(ui, cw)

    if 'fsmonitor' in runsteps:
        _checkfsmonitor(ui, cw, hgversion)

    if 'blackbox' in runsteps:
        _promptnativeextension(ui, cw, 'blackbox',
                               'Enable logging of commands to help diagnose bugs '
                               'and performance problems')

    if 'security' in runsteps:
        _checksecurity(ui, cw, hgversion)

    if 'firefoxtree' in runsteps:
        _promptvctextension(ui, cw, 'firefoxtree', FIREFOXTREE_INFO)

    if 'wip' in runsteps:
        _checkwip(ui, cw)

    if 'codereview' in runsteps:
        _checkcodereview(ui, cw)

    if 'pushtotry' in runsteps:
        _promptvctextension(ui, cw, 'push-to-try', PUSHTOTRY_INFO)

    if 'multiplevct' in runsteps:
        _checkmultiplevct(ui, cw)

    if 'configchange' in runsteps:
        _handleconfigchange(ui, cw)

    if 'permissions' in runsteps:
        _checkpermissions(ui, cw)

    return 0


# Older versions of Mercurial don't support the "optionalrepo" named
# argument on the command decorator. While we don't support these older
# versions of Mercurial, this could cause extension loading to fail.
# So we handle the error to enable the extension to load and the command
# to run.
cwargs = [
    ('s', 'statedir', '', _('directory to store state')),
]
try:
    configwizard = command('configwizard', cwargs, _('hg configwizard'),
                           optionalrepo=True)(configwizard)
except TypeError:
    from mercurial import commands

    # We can get TypeError for multiple reasons:
    #
    # 1. optionalrepo named argument not accepted
    # 2. command is None

    if command:
        configwizard = command('configwizard', cwargs, _('hg configwizard'))(configwizard)
        commands.optionalrepo += ' configwizard'
    else:
        commands.table['configwizard'] = (
            configwizard, cwargs, _('hg configwizard')
        )
        commands.optionalrepo += ' configwizard'


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

    if uipromptchoice(ui, 'Would you like to continue using an old Mercurial version (Yn)? $$ &Yes $$ &No'):
        return 1


def uiprompt(ui, msg, default=None):
    """Wrapper for ui.prompt() that only renders the last line of text as prompt.

    This prevents entire prompt text from rendering as a special color which
    may be hard to read.
    """
    lines = msg.splitlines(True)
    ui.write(''.join(lines[0:-1]))
    return ui.prompt(lines[-1], default=default)


def uipromptchoice(ui, msg, default=0):
    lines = msg.splitlines(True)
    ui.write(''.join(lines[0:-1]))
    return ui.promptchoice(lines[-1], default=default)


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

    if not uipromptchoice(ui, '%s (Yn) $$ &Yes $$ &No' % msg):
        if 'extensions' not in cw.c:
            cw.c['extensions'] = {}

        cw.c['extensions'][ext] = ''


def _vctextpath(ext, path=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.normpath(os.path.join(here, '..'))
    ext_path = os.path.join(ext_dir, ext)
    if path:
        ext_path = os.path.join(ext_path, path)

    return ext_path


def _enableext(cw, name, value):
    if 'extensions' not in cw.c:
        cw.c['extensions'] = {}

    cw.c['extensions'][name] = value


def _promptvctextension(ui, cw, ext, msg):
    if ui.hasconfig('extensions', ext):
        return

    ext_path = _vctextpath(ext)

    # Verify the extension loads before prompting to enable it. This is
    # done out of paranoia.

    # Even if we launch hg.exe, sys.argv[0] is "hg" on Windows. Since "hg" isn't
    # a Windows application, we can't simply run it. So change to the ".exe"
    # variant if necessary.
    hg = sys.argv[0]
    if sys.platform in ('win32', 'msys') and hg.endswith('hg'):
        hg += '.exe'

    result = subprocess.check_output([hg,
                                      '--config', 'extensions.testmodule=%s' % ext_path,
                                      '--config', 'ui.traceback=true'],
                                     stderr=subprocess.STDOUT)
    if 'Traceback' in result:
        return

    if uipromptchoice(ui, '%s (Yn) $$ &Yes $$ &No' % msg):
        return

    _enableext(cw, ext, ext_path)


def _checkcolor(ui, cw, hg_version):
    # Mercurial 4.2 has color built-in and enabled by default. We only enable
    # the extension on old versions. And we remove the extension on modern
    # versions.
    color_builtin = hg_version >= (4, 2, 0)

    if color_builtin:
        ext = cw.c.get('extensions', {})
        if 'color' in ext:
            ui.write('Removing extensions.color because color is enabled '
                     'by default in Mercurial 4.2+\n')
            del ext['color']
    else:
        _promptnativeextension(ui, cw, 'color',
                               'Enable color output to your terminal')


def _checkpager(ui, cw, hg_version):
    # Mercurial 4.2 has pager built-in and enabled by default. Furthermore,
    # the ``pager.attend-*`` config options are no longer needed on 4.2+ because
    # paging is enabled on a per-command basis.
    #
    # Presence of the legacy extension or config values triggers old behaviors.
    # So, when running on 4.2+ we delete old configs.
    #
    # The only config options that users may set in 4.2+ are ``pager.pager`` and
    # ``pager.ignore``. We don't remove these.
    pager_builtin = hg_version >= (4, 2, 0)

    if pager_builtin:
        ext = cw.c.get('extensions', {})
        if 'pager' in ext:
            ui.write('Removing extensions.pager because pager is built-in in '
                     'Mercurial 4.2+\n')
            del ext['pager']

        for k in list(cw.c.get('pager', {})):
            if not k.startswith('attend'):
                continue

            ui.write('Removing pager.%s because it is no longer necessary in '
                     'Mercurial 4.2+\n' % k)
            del cw.c['pager'][k]
    else:
        haveext = ui.hasconfig('extensions', 'pager')
        attends = set([
            'help',
            'incoming',
            'outgoing',
            'status',
        ])

        haveattends = all(ui.hasconfig('pager', 'attend-%s' % a) for a in attends)
        haveconfig = ui.hasconfig('pager', 'pager')

        if haveext and haveattends and haveconfig:
            return

        answer = uipromptchoice(ui, PAGER_INFO, default=0) + 1
        if answer == 3:
            return

        cw.c.setdefault('extensions', {})
        cw.c['extensions']['pager'] = ''

        if answer == 2:
            return

        cw.c.setdefault('pager', {})

        # Set the pager invocation to a more reasonable default than Mercurial's.
        # Don't overwrite user-specified value.
        #
        # -F quit if one screen
        # -R raw control chars
        # -S chop long lines instead of wrap
        # -Q quiet (no terminal bell)
        # -X no termcap init/deinit (won't clear screen afterwards)
        if not haveconfig:
            # Pager on Windows doesn't like passing environment variables as
            # part of the arguments. So pass explicit arguments there.
            # TODO justify merits of using ``LESS`` at all. Does it provide
            # any advantages?
            if sys.platform.startswith(('win32', 'msys')):
                value = 'less -FRSXQ'
            else:
                value = 'LESS=FRSXQ less'

            cw.c['pager']['pager'] = value

        for a in sorted(attends):
            if not ui.hasconfig('pager', 'attend-%s' % a):
                cw.c['pager']['attend-%s' % a] = 'true'


def _checkcurses(ui, cw):
    if ui.hasconfig('ui', 'interface'):
        return

    # curses isn't available on all platforms. Don't prompt if not
    # available.
    with demandimport.deactivated():
        try:
            import curses
        except Exception:
            try:
                import wcurses
            except Exception:
                return

    if ui.promptchoice(CURSES_INFO):
        return

    cw.c.setdefault('ui', {})
    cw.c['ui']['interface'] = 'curses'


def _checkhistoryediting(ui, cw):
    if all(ui.hasconfig('extensions', e) for e in ('histedit', 'rebase')):
        return

    if ui.promptchoice('Enable history rewriting commands (Yn)? $$ &Yes $$ &No'):
        return

    if 'extensions' not in cw.c:
        cw.c['extensions'] = {}

    cw.c['extensions']['histedit'] = ''
    cw.c['extensions']['rebase'] = ''


def _checkfsmonitor(ui, cw, hgversion):
    # fsmonitor came into existence in Mercurial 3.8. Before that, it
    # was the "hgwatchman" extension from a 3rd party repository.
    # Instead of dealing with installing hgwatchman, we version sniff
    # and print a message about wanting a more modern Mercurial version.

    watchman = 'watchman'
    if sys.platform in ('win32', 'msys'):
        watchman = 'watchman.exe'

    try:
        subprocess.check_output([watchman, '--version'],
                                stderr=subprocess.STDOUT)
    except Exception:
        ui.write(WATCHMAN_NOT_FOUND)
        ui.write('\n')
        return

    if ui.hasconfig('extensions', 'fsmonitor'):
        ext = cw.c.get('extensions', {})
        if any([ext.pop('hgwatchman', False), ext.pop('watchman', False)]):
            ui.write('Removing extensions.hgwatchman because fsmonitor is installed\n')

        return

    # Mercurial 3.8+ has fsmonitor built-in.
    if hgversion >= (3, 8, 0):
        _promptnativeextension(ui, cw, 'fsmonitor', FSMONITOR_INFO)
    else:
        ui.write(FSMONITOR_NOT_AVAILABLE)


def _checkwip(ui, cw):
    havewip = ui.hasconfig('alias', 'wip')

    if not havewip and ui.promptchoice(WIP_INFO):
        return

    # The wip configuration changes over time. Ensure it is up to date.
    cw.c.setdefault('alias', {})
    cw.c.setdefault('revsetalias', {})
    cw.c.setdefault('templates', {})

    cw.c['alias']['wip'] = 'log --graph --rev=wip --template=wip'


    wiprevset = ('('
                'parents(not public()) '
                'or not public() '
                'or . '
                'or (head() and branch(default))'
            ') and (not obsolete() or unstable()^) '
            'and not closed()')

    if ui.hasconfig('extensions', 'firefoxtree') or 'firefoxtree' in cw.c.get('extensions', {}):
        wiprevset += ' and not (fxheads() - date(-90))'

    cw.c['revsetalias']['wip'] = wiprevset

    cw.c['templates']['wip'] = (
        "'"
        # branches
        '{label("wip.branch", if(branches,"{branches} "))}'
        # revision and node
        '{label(ifeq(graphnode,"x","wip.obsolete","wip.{phase}"),"{rev}:{node|short}")}'
        # just the username part of the author, for brevity
        '{label("wip.user", " {author|user}")}'
        # tags
        '{label("wip.tags", if(tags," {tags}"))}'
        '{label("wip.tags", if(fxheads," {fxheads}"))}'
        # bookmarks (taking care to not underline the separator)
        '{if(bookmarks," ")}'
        '{label("wip.bookmarks", if(bookmarks,bookmarks))}'
        # first line of commit message
        '{label(ifcontains(rev, revset("parents()"), "wip.here"), " {desc|firstline}")}'
        "'"
    )

    # Set the colors for the parts of the WIP output.
    _set_color(cw, 'wip.bookmarks', 'yellow underline')
    _set_color(cw, 'wip.branch', 'yellow')
    _set_color(cw, 'wip.draft', 'green')
    _set_color(cw, 'wip.here', 'red')
    _set_color(cw, 'wip.obsolete', 'none')
    _set_color(cw, 'wip.public', 'blue')
    _set_color(cw, 'wip.tags', 'yellow')
    _set_color(cw, 'wip.user', 'magenta')

    # Enabling graphshorten greately improves the graph output.
    if 'experimental' not in cw.c:
        cw.c['experimental'] = {}
    cw.c['experimental']['graphshorten'] = 'true'

    # wip is paged automatically if pager is built-in... unless the pager
    # extension is enabled. So we set ``pager.attend-wip`` iff the pager
    # extension is present.
    if 'pager' in cw.c.get('extensions', {}):
        cw.c.setdefault('pager', {})
        cw.c['pager']['attend-wip'] = 'true'


def _set_color(cw, name, value):
    """ Set colors without overriding existing values. """
    if 'color' not in cw.c:
        cw.c['color'] = {}
    if name not in cw.c['color']:
        cw.c['color'][name] = value


def _checksecurity(ui, cw, hgversion):
    import ssl

    # Python + Mercurial didn't have terrific TLS handling until Python
    # 2.7.9 and Mercurial 3.4. For this reason, it was recommended to pin
    # certificates in Mercurial config files. In modern versions of
    # Mercurial, the system CA store is used and old, legacy TLS protocols
    # are disabled. The default connection/security setting should
    # be sufficient and pinning certificates is no longer needed.

    hg39 = util.versiontuple(n=2) >= (3, 9)
    modernssl = hasattr(ssl, 'SSLContext')

    def setfingerprints(porting=False):
        # Need to process in sorted order for tests to be deterministic.
        if hg39:
            cw.c.setdefault('hostsecurity', {})
            for k, v in sorted(MODERN_FINGERPRINTS.items()):
                if porting and k not in cw.c.get('hostfingerprints', {}):
                    continue

                cw.c['hostsecurity']['%s:fingerprints' % k] = v
        else:
            cw.c.setdefault('hostfingerprints', {})
            for k, v in sorted(HOST_FINGERPRINTS.items()):
                if porting and k not in cw.c['hostfingerprints']:
                    continue

                cw.c['hostfingerprints'][k] = v

    if not modernssl:
        setfingerprints()

    # We always update fingerprints if they are present. We /could/ offer to
    # remove fingerprints if running modern Python and Mercurial. But that
    # just adds more UI complexity and isn't worth it.
    have_legacy = any(k in cw.c.get('hostfingerprints', {})
                      for k in HOST_FINGERPRINTS)
    have_modern = any('%s:fingerprints' % k in cw.c.get('hostsecurity', {})
                      for k in MODERN_FINGERPRINTS)

    if have_legacy or have_modern:
        setfingerprints(porting=True)

    # If we're using Mercurial 3.9, remove legacy fingerprints if they
    # are present.
    if have_legacy and hg39:
        for k in HOST_FINGERPRINTS:
            try:
                del cw.c['hostfingerprints'][k]
            except KeyError:
                pass

        # Delete empty config section.
        if 'hostfingerprints' in cw.c and not cw.c['hostfingerprints']:
            del cw.c['hostfingerprints']


def _checkcodereview(ui, cw):
    # We don't check for bzexport if reviewboard is enabled because
    # bzexport is legacy.
    if ui.hasconfig('extensions', 'reviewboard'):
        return

    if ui.promptchoice('Will you be submitting commits to Mozilla (Yn)? $$ &Yes $$ &No'):
        return

    confrb = False
    answer = uipromptchoice(ui, CODEREVIEW_INFO, default=0) + 1
    if answer in (1, 2):
        _enableext(cw, 'reviewboard', _vctextpath('reviewboard', 'client.py'))
        confrb = True

    if answer in (2, 3):
        _enableext(cw, 'bzexport', _vctextpath('bzexport'))

    # Now verify Bugzilla credentials and other config foo is set.
    bzuser = ui.config('bugzilla', 'username')
    bzapikey = ui.config('bugzilla', 'apikey')

    if not bzuser or not bzapikey:
        ui.write(MISSING_BUGZILLA_CREDENTIALS)

    if not bzuser:
        bzuser = ui.prompt('What is your Bugzilla email address? (optional)', default='')

    if bzuser and not bzapikey:
        ui.write(BUGZILLA_API_KEY_INSTRUCTIONS)
        bzapikey = ui.prompt('Please enter a Bugzilla API Key: (optional)', default='')


    if any(ui.hasconfig('bugzilla', c) for c in ('password', 'userid', 'cookie')):
        ui.write(LEGACY_BUGZILLA_CREDENTIALS_DETECTED)

    for c in ('password', 'userid', 'cookie'):
        try:
            del cw.c['bugzilla'][c]
        except KeyError:
            pass

    prompt = ('Configure the "review" path so you can `hg push review` commits to '
             'Mozilla for review (Yn)? $$ &Yes $$ &No')
    if not ui.config('paths', 'review') and not ui.promptchoice(prompt):
        cw.c.setdefault('paths', {})
        cw.c['paths']['review'] = 'https://reviewboard-hg.mozilla.org/autoreview'

    if not ui.config('mozilla', 'ircnick'):
        ircnick = ui.prompt('What is your IRC nick? ', default=None)
        if ircnick:
            cw.c.setdefault('mozilla', {})
            cw.c['mozilla']['ircnick'] = ircnick

    if bzuser or bzapikey:
        if 'bugzilla' not in cw.c:
            cw.c['bugzilla'] = {}

    if bzuser:
        cw.c['bugzilla']['username'] = bzuser
    if bzapikey:
        cw.c['bugzilla']['apikey'] = bzapikey


def _checkmultiplevct(ui, cw):
    # References to multiple version-control-tools checkouts can confuse
    # version-control-tools since various Mercurial extensions resolve
    # dependencies via __file__. Files from different revisions could lead
    # to unexpected environments and break things.
    seenvct = set()
    for k, v in ui.configitems('extensions'):
        # mercurial.extensions.loadpath() does variable and user expansion.
        # We need to match behavior.
        v = os.path.realpath(util.normpath(util.expandpath(v)))

        if 'version-control-tools' not in v:
            continue
        i = v.index('version-control-tools')
        vct = v[0:i + len('version-control-tools')]
        seenvct.add(vct)

    if len(seenvct) > 1:
        ui.write(MULTIPLE_VCT % cw.path)


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


def _checkpermissions(ui, cw):
    # Config file may contain sensitive content, such as API keys. Prompt to
    # remove global permissions.
    if sys.platform == 'win32':
        return

    mode = os.stat(cw.path).st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        if uipromptchoice(ui, FILE_PERMISSIONS_WARNING):
            return

        # We don't care about sticky and set UID bits because
        # this is a regular file.
        mode = mode & stat.S_IRWXU
        ui.write('Changing permissions of %s\n' % cw.path)
        os.chmod(cw.path, mode)


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


# Ancient versions of Mercurial lack util.safehasattr(). So implement it here.
_notset = object()
def safehasattr(thing, attr):
    return getattr(thing, attr, _notset) is not _notset


def uisetup(ui):
    # hasconfig() was added in 3.7. Backport until we require 3.7.
    if safehasattr(ui, 'hasconfig'):
        return

    class configui(ui.__class__):
        def hasconfig(self, section, name, untrusted=False):
            return name in self._data(untrusted)._data.get(section, {})

    ui.__class__ = configui
    uimod.ui = configui


def extsetup(ui):
    # util.versiontuple was added in 3.6. Backport it.
    def versiontuple(v=None, n=4):
        if not v:
            v = util.version()
        parts = v.split('+', 1)
        if len(parts) == 1:
            vparts, extra = parts[0], None
        else:
            vparts, extra = parts

        vints = []
        for i in vparts.split('.'):
            try:
                vints.append(int(i))
            except ValueError:
                break
        # (3, 6) -> (3, 6, None)
        while len(vints) < 3:
            vints.append(None)

        if n == 2:
            return (vints[0], vints[1])
        if n == 3:
            return (vints[0], vints[1], vints[2])
        if n == 4:
            return (vints[0], vints[1], vints[2], extra)

    if not safehasattr(util, 'versiontuple'):
        util.versiontuple = versiontuple
