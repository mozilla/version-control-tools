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
    hg,
    pycompat,
    ui as uimod,
    util,
)
from mercurial.i18n import _
from mercurial.commands import (
    pull as hgpull,
    update as hgupdate,
)

OUR_DIR = os.path.dirname(__file__)
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

from configobj import ConfigObj


HOST_FINGERPRINTS = {
    'bitbucket.org': '3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa',
    'bugzilla.mozilla.org': '7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17',
    'hg.mozilla.org': '1c:a5:7d:a1:28:db:78:f6:52:4d:c0:e6:38:9b:08:43:ec:1f:ef:64',
}

MODERN_FINGERPRINTS = {
    'bitbucket.org': 'sha256:4e:65:3e:76:0f:81:59:85:5b:50:06:0c:c2:4d:3c:56:53:8b:83:3e:9b:fa:55:26:98:9a:ca:e2:25:03:92:47',
    'bugzilla.mozilla.org': 'sha256:95:BA:0F:F2:C4:28:75:9D:B5:DB:4A:50:5F:29:46:A3:A9:4E:1B:56:A5:AE:10:50:C3:DD:3A:AC:73:BF:4A:D9',
    'hg.mozilla.org': 'sha256:17:38:aa:92:0b:84:3e:aa:8e:52:52:e9:4c:2f:98:a9:0e:bf:6c:3e:e9:15:ff:0a:29:80:f7:06:02:5b:e8:48',
}

INITIAL_MESSAGE = b'''
This wizard will guide you through configuring Mercurial for an optimal
experience contributing to Mozilla projects.

The wizard makes no changes without your permission.

To begin, press the enter/return key.
'''.lstrip()

MINIMUM_SUPPORTED_VERSION = (3, 5, 0)

# Upgrade Mercurial older than this.
# This should match MODERN_MERCURIAL_VERSION from
# mozilla-central/python/mozboot/mozboot/base.py
OLDEST_NON_LEGACY_VERSION = (4, 3, 3)

VERSION_TOO_OLD = b'''
Your version of Mercurial (%d.%d) is too old to run `hg configwizard`.

Mozilla's Mercurial support policy is to support at most the past
1 year of Mercurial releases (or 4 major Mercurial releases).

Please upgrade to Mercurial %d.%d or newer and try again.

See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
for Mozilla-tailored instructions for install Mercurial.
'''.lstrip()

LEGACY_MERCURIAL_MESSAGE = b'''
You are running an out of date Mercurial client (%s).

For a faster and better Mercurial experience, we HIGHLY recommend you
upgrade.

Legacy versions of Mercurial have known security vulnerabilities. Failure
to upgrade may leave you exposed. You are highly encouraged to upgrade in
case you aren't running a patched version.
'''.lstrip()

MISSING_USERNAME = b'''
You don't have a username defined in your Mercurial config file. In order
to author commits, you'll need to define a name and e-mail address.

This data will be publicly available when you send commits/patches to others.
If you aren't comfortable giving us your full name, pseudonames are
acceptable.

(Relevant config option: ui.username)
'''.lstrip()

MISSING_IRCNICK = b'''
You don't have a Mozilla IRC nickname defined in your Mercurial config file.

(Relevant config option: mozilla.ircnick)
'''

BAD_DIFF_SETTINGS = b'''
Mercurial is not configured to produce diffs in a more readable format.

Would you like to change this (Yn)? $$ &Yes $$ &No
'''.strip()

TWEAKDEFAULTS_INFO = b'''
Mercurial has implemented some functionality behind ui.tweakdefaults config,
that most users would like by default, but would break some workflows due to
backwards compatibility issues.
You can find more info by running:

  $ hg help config.ui

and checking the "tweakdefaults" section.

Would you like to enable these features (Yn)? $$ &Yes $$ &No
'''.strip()

PAGER_INFO = b'''
The "pager" extension transparently redirects command output to a pager
program (like "less") so command output can be more easily consumed
(e.g. output longer than the terminal can be scrolled).

Please select one of the following for configuring pager:

  1. Enable pager and configure with recommended settings (preferred)
  2. Enable pager with default configuration
  3. Don't enable pager

Which option would you like? $$ &1 $$ &2 $$ &3
'''.strip()

CURSES_INFO = b'''
Mercurial can provide richer terminal interactions for some operations
by using the popular "curses" library.

Would you like to enable "curses" interfaces (Yn)? $$ &Yes $$ &No
'''.strip()

EVOLVE_INCOMPATIBLE = b'''
Evolve requires Mercurial 4.3+. Your Mercurial is too old to run evolve.

Please upgrade Mercurial to use evolve.
'''.lstrip()

WATCHMAN_NOT_FOUND = b'''
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

FSMONITOR_INFO = b'''
The fsmonitor extension integrates the watchman filesystem watching tool
with Mercurial. Commands like `hg status`, `hg diff`, and `hg commit`
(which need to examine filesystem state) can query watchman to obtain
this state, allowing these commands to complete much quicker.

When installed, the fsmonitor extension will automatically launch a
background watchman daemon for accessed Mercurial repositories. It
should "just work."

Would you like to enable fsmonitor (Yn)? $$ &Yes $$ &No
'''.strip()

FSMONITOR_NOT_AVAILABLE = b'''
Newer versions of Mercurial have built-in support for integrating with
filesystem watching services to make common operations faster.

This integration is STRONGLY RECOMMENDED when using the Firefox
repository.

Please upgrade to Mercurial 3.8+ so this feature is available.
'''.lstrip()

WIP_INFO = b'''
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

WIP_UPDATED_EXPRESSION = b'''
It appears you are on a new version of Mercurial (4.6+) but you are using the old `hg wip` alias.
In new versions of Mercurial, the revset expression `unstable` has been renamed to `orphan`.

We will update the alias for you so it uses the new keyword.
'''.lstrip()

SMARTANNOTATE_INFO = b'''
The ``hg smart-annotate`` command provides experimental support for
viewing the annotate information while skipping certain changesets,
such as code-formatting changes.

Would you like to install the `hg smart-annotate` alias (Yn)? $$ &Yes $$ &No
'''.strip()

FIREFOXTREE_INFO = b'''
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

CLANG_FORMAT_INFO = b'''
The "clang-format" extension provides execution of clang-format at the commit steps.
It relies on ./mach clang-format directly.
Would you like to activate clang-format (Yn)? $$ &Yes $$ &No
'''.strip()

JS_FORMAT_INFO = b'''
The "js-format" extension provides execution of eslint+prettier at the commit steps.
It relies on ./mach eslint --fix directly.
Would you like to activate js-format (Yn)? $$ &Yes $$ &No
'''.strip()

FORMATSOURCE_INFO = b'''
The "format-source" extension provides a way to run code-formatting tools in a way that
avoids conflicts related to this formatting when merging/rebasing code across the
reformatting.
An example of a .hgrc configuration that uses our embedded clang-format and prettier-format
utilities from 'mach' is as follows:
[format-source]
clang-format = [Path To Mozilla Repo]/mach clang-format --assume-filename $HG_FILENAME -p
clang-format:configpaths = .clang-format, .clang-format-ignore
clang-format:fileext = .cpp, .c, .h
prettier-format = [Path To Mozilla Repo]/mach prettier-format --assume-filename $HG_FILENAME -p
prettier-format:configpaths = .prettierrc, .prettierignore
prettier-format:fileext = .js, .jsx, .jsm

If `clang-format` or `prettier-format` are not present under `[format-source]`, a default
configuration will be used that is embedded in this extension. The default configuration
can be used in most cases.
Would you like to activate format-source (Yn)? $$ &Yes $$ &No
'''.strip()

FORMATSOURCE_DISABLE_INFO = b'''
Removing extensions.format-source since it\'s no longer needed. For the moment we
want to disable format-source since the big format of Gecko has been performed.
We will re-enable this when we will need it again.\n
'''

CODEREVIEW_INFO = b'''
Commits to Mozilla projects are typically sent to Phabricator. This is the
preferred code review tool at Mozilla.
Phabricator installation instructions are here
http://moz-conduit.readthedocs.io/en/latest/phabricator-user.html

'''.lstrip()

PUSHTOTRY_INFO = b'''
The push-to-try extension generates a temporary commit with a given
try syntax and pushes it to the try server. The extension is intended
to be used in concert with other tools generating try syntax so that
they can push to try without depending on mq or other workarounds.

(Relevant config option: extensions.push-to-try)

Would you like to activate push-to-try (Yn)? $$ &Yes $$ &No
'''.strip()

HISTORY_EDITING_INFO = b'''
Various extensions provide functionality to rewrite repository history. These
enable more powerful - and often more productive - workflows.

If history rewriting is enabled, the following extensions will be enabled:

absorb
   `hg absorb` automatically squashes/folds uncommitted changes in the working
   directory into the appropriate previous changeset. Learn more at
   https://gregoryszorc.com/blog/2018/11/05/absorbing-commit-changes-in-mercurial-4.8/.

histedit
   `hg histedit` allows interactive editing of previous changesets. It presents
   you a list of changesets and allows you to pick actions to perform on each
   changeset. Actions include reordering changesets, dropping changesets,
   folding multiple changesets together, and editing the commit message for
   a changeset.

rebase
   `hg rebase` allows re-parenting changesets from one "branch" of a DAG
   to another. The command is typically used to "move" changesets based on
   an older changeset to be based on the newest changeset.

Would you like to enable these history editing extensions (Yn)? $$ &Yes $$ &No
'''.strip()


EVOLVE_INFO_WARNING = b'''
The evolve extension is a Mercurial extension for faster and
safer mutable history. It implements the changeset evolution concept
for Mercurial, allowing for safe and simple history re-writing. It
includes some new commands such as fold, prune and amend which may
improve your user experience with Mercurial.

The evolve extension is recommended for working with Firefox repositories.
More information about changeset evolution can be found by running:

  $ hg help evolution

as well as:

  $ hg help -e evolve

once the `evolve` extension is enabled.

(Relevant config option: extensions.evolve)

Would you like to enable the evolve extension? (Yn) $$ &Yes $$ &No
'''

EVOLVE_UPDATE_PROMPT = b'''
It looks like the setup wizard has already installed a copy of the
evolve extension on your machine, at {evolve_dir}.

(Relevant config option: extensions.evolve)

Would you like to update evolve to the latest version?  (Yn) $$ &Yes $$ &No
'''

EVOLVE_CLONE_ERROR = b'''
Could not clone the evolve extension for installation.
You can install evolve yourself with

  $ pip install --user hg-evolve

and then enable the extension via

  $ hg config -e
'''

MULTIPLE_VCT = b'''
*** WARNING ***

Multiple version-control-tools repositories are referenced in your
Mercurial config. Extensions and other code within the
version-control-tools repository could run with inconsistent results.

Please manually edit the following file to reference a single
version-control-tools repository:

    %s

'''.lstrip()

FILE_PERMISSIONS_WARNING = b'''
Your hgrc file is currently readable by others.

Sensitive information such as your Bugzilla credentials could be
stolen if others have access to this file/machine.

Would you like to fix the file permissions (Yn) $$ &Yes $$ &No
'''.strip()


testedwith = b'4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0'
buglink = b'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20configwizard'

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

try:
    from mercurial import registrar
except ImportError:
    registrar = None

try:
    from mercurial import configitems
except ImportError:
    configitems = None


def _vcthome():  # Returns the directory where the vct clone is located
    here = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.normpath(os.path.join(here, '..'))
    vct_dir = os.path.normpath(os.path.join(ext_dir, '..'))
    vcthome_dir = os.path.normpath(os.path.join(vct_dir, '..'))

    return pycompat.bytestr(vcthome_dir)


if registrar and util.safehasattr(registrar, b'configitem'):
    configtable = {}
    configitem = registrar.configitem(configtable)

    # TODO some of these are registered elsewhere. This can produce a warning
    # for duplicate registration. We should ideally call a shared function
    # that only registers once.
    configitem(b'configwizard', b'steps',
               default=[])
    configitem(b'bugzilla', b'username',
               default=None)
    configitem(b'bugzilla', b'apikey',
               default=None)
    configitem(b'mozilla', b'ircnick',
               default=None)
    configitem(b'mozilla', b'mozbuild_state_path',
               default=_vcthome())
    configitem(b'revsetalias', b'wip',
               default=None)

wizardsteps = set([
    b'hgversion',
    b'username',
    b'tweakdefaults',
    b'diff',
    b'color',
    b'pager',
    b'curses',
    b'historyediting',
    b'evolve',
    b'fsmonitor',
    b'blackbox',
    b'security',
    b'firefoxtree',
    b'format-source',
    b'wip',
    b'smartannotate',
    b'codereview',
    b'pushtotry',
    b'multiplevct',
    b'configchange',
    b'permissions',
    b'clang-format',
    b'js-format',
    b'shelve',
])


def configwizard(ui, repo, statedir=None, **opts):
    """Ensure your Mercurial configuration is up to date."""
    runsteps = set(wizardsteps)

    # Mercurial <1.7 had a bug where monkeypatching ui.__class__
    # during uisetup() doesn't work. So we do our own ui.hasconfig()
    # here. Other uses of ui.hasconfig() are allowed, as they will
    # have a properly monkeypatched ui.__class__.
    if b'steps' in ui._data(False)._data.get(b'configwizard', {}):
        runsteps = set(ui.configlist(b'configwizard', b'steps'))

    hgversion = util.versiontuple(n=3)

    # The point release version can be None for e.g. X.Y versions. Normalize
    # to make tuple compares work.
    if hgversion[2] is None:
        hgversion = (hgversion[0], hgversion[1], 0)

    if hgversion < MINIMUM_SUPPORTED_VERSION:
        ui.warn(VERSION_TOO_OLD % (
            hgversion[0], hgversion[1],
            MINIMUM_SUPPORTED_VERSION[0], MINIMUM_SUPPORTED_VERSION[1],
        ))
        raise error.Abort(b'upgrade Mercurial then run again')

    uiprompt(ui, INITIAL_MESSAGE, default=b'<RETURN>')

    with demandimport.deactivated():
        # Mercurial 4.2 moved function from scmutil to rcutil.
        try:
            from mercurial.rcutil import userrcpath
        except ImportError:
            from mercurial.scmutil import userrcpath

    configpaths = [p for p in userrcpath() if os.path.exists(p)]
    path = configpaths[0] if configpaths else userrcpath()[0]
    cw = configobjwrapper(path)

    if b'hgversion' in runsteps:
        if _checkhgversion(ui, hgversion):
            return 1

    if b'username' in runsteps:
        _checkusername(ui, cw)

    if b'tweakdefaults' in runsteps:
        _checktweakdefaults(ui, cw)

    if b'diff' in runsteps:
        _checkdiffsettings(ui, cw)

    if b'color' in runsteps:
        _checkcolor(ui, cw, hgversion)

    if b'pager' in runsteps:
        _checkpager(ui, cw, hgversion)

    if b'curses' in runsteps:
        _checkcurses(ui, cw)

    if b'historyediting' in runsteps:
        _checkhistoryediting(ui, cw, hgversion)

    if b'evolve' in runsteps:
        _checkevolve(ui, cw, hgversion)

    if b'fsmonitor' in runsteps:
        _checkfsmonitor(ui, cw, hgversion)

    if b'blackbox' in runsteps:
        _promptnativeextension(ui, cw, b'blackbox',
                               b'Enable logging of commands to help diagnose bugs '
                               b'and performance problems')

    if b'shelve' in runsteps:
        _promptnativeextension(ui, cw, b'shelve',
                               b'Enable the shelve feature. Equivalent to git stash')

    if b'security' in runsteps:
        _checksecurity(ui, cw, hgversion)

    if b'firefoxtree' in runsteps:
        _promptvctextension(ui, cw, b'firefoxtree', FIREFOXTREE_INFO)

    if b'clang-format' in runsteps:
        _promptvctextension(ui, cw, b'clang-format', CLANG_FORMAT_INFO)

    if b'js-format' in runsteps:
        _promptvctextension(ui, cw, b'js-format', JS_FORMAT_INFO)


    if b'format-source' in runsteps:
        _checkformatsource(ui, cw)

    if b'wip' in runsteps:
        _checkwip(ui, cw)

    if b'smartannotate' in runsteps:
        _checksmartannotate(ui, cw)

    if b'codereview' in runsteps:
        _checkcodereview(ui, cw)

    if b'pushtotry' in runsteps:
        _promptvctextension(ui, cw, b'push-to-try', PUSHTOTRY_INFO)

    if b'multiplevct' in runsteps:
        _checkmultiplevct(ui, cw)

    if b'configchange' in runsteps:
        _handleconfigchange(ui, cw)

    if b'permissions' in runsteps:
        _checkpermissions(ui, cw)

    return 0


# Older versions of Mercurial don't support the "optionalrepo" named
# argument on the command decorator. While we don't support these older
# versions of Mercurial, this could cause extension loading to fail.
# So we handle the error to enable the extension to load and the command
# to run.
cwargs = [
    (b's', b'statedir', b'', _(b'directory to store state')),
]
try:
    configwizard = command(b'configwizard', cwargs, _(b'hg configwizard'),
                           optionalrepo=True)(configwizard)
except TypeError:
    from mercurial import commands

    # We can get TypeError for multiple reasons:
    #
    # 1. optionalrepo named argument not accepted
    # 2. command is None

    if command:
        configwizard = command(b'configwizard', cwargs, _(b'hg configwizard'))(configwizard)
        commands.optionalrepo += b' configwizard'
    else:
        commands.table[b'configwizard'] = (
            configwizard, cwargs, _(b'hg configwizard')
        )
        commands.optionalrepo += b' configwizard'


def _checkhgversion(ui, hgversion):
    if hgversion >= OLDEST_NON_LEGACY_VERSION:
        return

    ui.warn(LEGACY_MERCURIAL_MESSAGE % util.version())
    ui.warn(b'\n')

    if os.name == 'nt':
        ui.warn(b'Please upgrade to the latest MozillaBuild to upgrade '
                b'your Mercurial install.\n\n')
    else:
        ui.warn(b'Please run `mach bootstrap` to upgrade your Mercurial '
                b'install.\n\n')

    if uipromptchoice(ui, b'Would you like to continue using an old Mercurial version (Yn)? $$ &Yes $$ &No'):
        return 1


def uiprompt(ui, msg, default=None):
    """Wrapper for ui.prompt() that only renders the last line of text as prompt.

    This prevents entire prompt text from rendering as a special color which
    may be hard to read.
    """
    lines = msg.splitlines(True)
    ui.write(b''.join(lines[0:-1]))
    return ui.prompt(lines[-1], default=default)


def uipromptchoice(ui, msg, default=0):
    lines = msg.splitlines(True)
    ui.write(b''.join(lines[0:-1]))
    return ui.promptchoice(lines[-1], default=default)


def _checkusername(ui, cw):
    if ui.config(b'ui', b'username'):
        return

    ui.write(MISSING_USERNAME)

    name, email = None, None

    name = ui.prompt(b'What is your name?', b'')
    if name:
        email = ui.prompt(b'What is your e-mail address?', b'')

    if name and email:
        username = b'%s <%s>' % (name, email)
        if 'ui' not in cw.c:
            cw.c['ui'] = {}
        cw.c['ui']['username'] = pycompat.sysstr(username.strip())

        ui.write(b'setting ui.username=%s\n\n' % username)
    else:
        ui.warn(b'Unable to set username; You will be unable to author '
                b'commits\n\n')


def _checkdiffsettings(ui, cw):
    git = ui.configbool(b'diff', b'git')
    showfunc = ui.configbool(b'diff', b'showfunc')

    if git and showfunc:
        return

    if not uipromptchoice(ui, BAD_DIFF_SETTINGS):
        if 'diff' not in cw.c:
            cw.c['diff'] = {}

        cw.c['diff']['git'] = 'true'
        cw.c['diff']['showfunc'] = 'true'


def _checktweakdefaults(ui, cw):
    if ui.configbool(b'ui', b'tweakdefaults'):
        return

    if not uipromptchoice(ui, TWEAKDEFAULTS_INFO):
        if 'ui' not in cw.c:
            cw.c['ui'] = {}

        cw.c['ui']['tweakdefaults'] = 'true'

        # Determine if curses is available on the system
        # and use the text interface if unavailable
        if not _try_curses_import():
            cw.c['ui']['interface'] = 'text'


def _promptnativeextension(ui, cw, ext, msg):
    if ui.hasconfig(b'extensions', ext):
        return

    if not uipromptchoice(ui, b'%s (Yn) $$ &Yes $$ &No' % msg):
        if b'extensions' not in cw.c:
            cw.c['extensions'] = {}

        cw.c['extensions'][pycompat.sysstr(ext)] = ''


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
    if ui.hasconfig(b'extensions', ext):
        return

    ext_path = _vctextpath(pycompat.sysstr(ext))

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
    if b'Traceback' in result:
        return

    if uipromptchoice(ui, b'%s (Yn) $$ &Yes $$ &No' % msg):
        return

    _enableext(cw, pycompat.sysstr(ext), ext_path)


def _checkcolor(ui, cw, hg_version):
    # Mercurial 4.2 has color built-in and enabled by default. We only enable
    # the extension on old versions. And we remove the extension on modern
    # versions.
    color_builtin = hg_version >= (4, 2, 0)

    if color_builtin:
        ext = cw.c.get('extensions', {})
        if 'color' in ext:
            ui.write(b'Removing extensions.color because color is enabled '
                     b'by default in Mercurial 4.2+\n')
            del ext['color']
    else:
        _promptnativeextension(ui, cw, b'color',
                               b'Enable color output to your terminal')


def _checkformatsource(ui, cw):
    disable_format_source = True

    if disable_format_source:
        ext = cw.c.get('extensions', {})
        if 'format-source' in ext:
            ui.write(FORMATSOURCE_DISABLE_INFO)
            del ext['format-source']
    else:
        _promptvctextension(ui, cw, b'format-source', FORMATSOURCE_INFO)


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
            ui.write(b'Removing extensions.pager because pager is built-in in '
                     b'Mercurial 4.2+\n')
            del ext['pager']

        for k in list(cw.c.get('pager', {})):
            if not k.startswith('attend'):
                continue

            ui.write(b'Removing pager.%s because it is no longer necessary in '
                     b'Mercurial 4.2+\n' % pycompat.bytestr(k))
            del cw.c['pager'][k]
    else:
        haveext = ui.hasconfig(b'extensions', b'pager')
        attends = set([
            b'help',
            b'incoming',
            b'outgoing',
            b'status',
        ])

        haveattends = all(ui.hasconfig(b'pager', b'attend-%s' % a) for a in attends)
        haveconfig = ui.hasconfig(b'pager', b'pager')

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
            if not ui.hasconfig(b'pager', b'attend-%s' % a):
                cw.c['pager']['attend-%s' % pycompat.sysstr(a)] = 'true'


def _try_curses_import():
    '''Attempt to import curses, returning `True`
    on success'''
    with demandimport.deactivated():
        try:
            import curses
        except Exception:
            try:
                import wcurses
            except Exception:
                return False

    return True


def _checkcurses(ui, cw):
    if ui.hasconfig(b'ui', b'interface'):
        return

    # curses isn't available on all platforms. Don't prompt if not
    # available.
    if _try_curses_import() and uipromptchoice(ui, CURSES_INFO):
        return

    cw.c.setdefault('ui', {})
    cw.c['ui']['interface'] = 'curses'


def _activate_inmemory_rebase(cw):
    '''Activates in-memory rebase.
    '''
    if 'rebase' not in cw.c:
        cw.c['rebase'] = {}

    cw.c['rebase']['experimental.inmemory'] = 'yes'

def _checkhistoryediting(ui, cw, hg_version):
    extensions = {b'histedit', b'rebase'}

    if hg_version >= (4, 8, 0):
        extensions.add(b'absorb')

    # Turn on in-memory rebase for those who have rebase on already
    if ui.hasconfig(b'extensions', b'rebase'):
        _activate_inmemory_rebase(cw)

    if all(ui.hasconfig(b'extensions', e) for e in extensions):
        return

    if uipromptchoice(ui, HISTORY_EDITING_INFO):
        return

    if 'extensions' not in cw.c:
        cw.c['extensions'] = {}

    for ext in sorted(extensions):
        cw.c['extensions'][pycompat.sysstr(ext)] = ''

    # Turn on in-memory rebase if a user wants rebase
    _activate_inmemory_rebase(cw)


def _checkevolve(ui, cw, hg_version):
    if hg_version < (4, 3, 0):
        ui.warn(EVOLVE_INCOMPATIBLE)
        return

    remote_evolve_path = b'https://www.mercurial-scm.org/repo/evolve/'
    # Install to the same dir as v-c-t, unless the mozbuild directory path is passed (testing)
    evolve_clone_dir = ui.config(b'mozilla', b'mozbuild_state_path', _vcthome())

    local_evolve_path = b'%(evolve_clone_dir)s/evolve' % {b'evolve_clone_dir': evolve_clone_dir}
    evolve_config_value = '%(evolve_path)s/hgext3rd/evolve' % \
                          {'evolve_path': pycompat.sysstr(local_evolve_path)}

    # If evolve is not installed, install it
    if not ui.hasconfig(b'extensions', b'evolve'):
        if uipromptchoice(ui, EVOLVE_INFO_WARNING):
            return

        try:
            # Clone the evolve extension and enable
            hg.clone(ui, {}, remote_evolve_path, branch=(b'stable',), dest=local_evolve_path)
            _enableext(cw, 'evolve', evolve_config_value)

            ui.write(b'Evolve was downloaded successfully.\n')

        except error.Abort as hg_err:
            ui.write(str(hg_err))
            ui.write(EVOLVE_CLONE_ERROR)

    # If evolve is installed and managed by this wizard,
    # update it via pull/update
    elif ui.config(b'extensions', b'evolve') == evolve_config_value:
        if uipromptchoice(ui, EVOLVE_UPDATE_PROMPT % {b'evolve_dir': local_evolve_path}):
            return

        try:
            local_evolve_repo = hg.repository(ui, local_evolve_path)

            # Pull the latest stable, update to tip
            hgpull(ui, local_evolve_repo, source=remote_evolve_path, branch=(b'stable',))
            hgupdate(ui, local_evolve_repo, rev=b'stable')

            ui.write(b'Evolve was updated successfully.\n')

        except error.Abort as hg_err:
            ui.write(EVOLVE_CLONE_ERROR)

    # If evolve is not managed by this wizard, do nothing
    else:
        return


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
        ui.write(b'\n')
        return

    if ui.hasconfig(b'extensions', 'fsmonitor'):
        ext = cw.c.get('extensions', {})
        if any([ext.pop('hgwatchman', False), ext.pop('watchman', False)]):
            ui.write(b'Removing extensions.hgwatchman because fsmonitor is installed\n')

        return

    # Mercurial 3.8+ has fsmonitor built-in.
    if hgversion >= (3, 8, 0):
        _promptnativeextension(ui, cw, b'fsmonitor', FSMONITOR_INFO)
    else:
        ui.write(FSMONITOR_NOT_AVAILABLE)


def _checkwip(ui, cw):
    havewip_alias = ui.hasconfig(b'alias', b'wip')
    havewip_revset = ui.hasconfig(b'revsetalias', b'wip')

    hg_version = util.versiontuple(n=2)

    # If the user has the `wip` revset alias, they are on hg46+ and have the old alias
    # (ie with `orphan` expression instead of `unstable`), we upgrade with a notice
    if havewip_revset and hg_version >= (4, 6) and b'unstable' in ui.config(b'revsetalias', b'wip'):
        ui.write(WIP_UPDATED_EXPRESSION)
    elif not havewip_alias and uipromptchoice(ui, WIP_INFO):
        return

    # The wip configuration changes over time. Ensure it is up to date.
    cw.c.setdefault('alias', {})
    cw.c.setdefault('revsetalias', {})
    cw.c.setdefault('templates', {})

    cw.c['alias']['wip'] = 'log --graph --rev=wip --template=wip'

    if hg_version < (4, 6):
        unstable = 'unstable'
    else:
        unstable = 'orphan'

    wiprevset = ('('
                'parents(not public()) '
                'or not public() '
                'or . '
                'or (head() and branch(default))'
            ') and (not obsolete() or %s()^) '
            'and not closed()') % unstable

    if ui.hasconfig(b'extensions', b'firefoxtree') or 'firefoxtree' in cw.c.get('extensions', {}):
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


def _checksmartannotate(ui, cw):
    havesmartannotate_alias = ui.hasconfig(b'alias', b'smart-annotate')

    if not havesmartannotate_alias and uipromptchoice(ui, SMARTANNOTATE_INFO):
        return

    cw.c.setdefault('alias', {})
    cw.c.setdefault('revsetalias', {})
    cw.c.setdefault('extdata', {})

    cw.c['alias']['smart-annotate'] = 'annotate -w --skip ignored_changesets'

    cw.c['revsetalias']['ignored_changesets'] = 'desc("ignore-this-changeset") or extdata(get_ignored_changesets)'

    cw.c['extdata']['get_ignored_changesets'] = (
        'shell:cat '
        '`hg root`/.hg-annotate-ignore-revs '
        '2> /dev/null || true'
    )


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
                old_key = k
                new_key = '%s:fingerprints' % k

                have_key = (old_key in cw.c.get('hostfingerprints', {})
                            or new_key in cw.c['hostsecurity'])

                if porting and not have_key:
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
    if ui.promptchoice(b'Will you be submitting commits to Mozilla (Yn)? $$ &Yes $$ &No'):
        return

    ui.write(CODEREVIEW_INFO)


def _checkmultiplevct(ui, cw):
    # References to multiple version-control-tools checkouts can confuse
    # version-control-tools since various Mercurial extensions resolve
    # dependencies via __file__. Files from different revisions could lead
    # to unexpected environments and break things.
    seenvct = set()
    for k, v in ui.configitems(b'extensions'):
        # mercurial.extensions.loadpath() does variable and user expansion.
        # We need to match behavior.
        v = os.path.realpath(util.normpath(util.expandpath(v)))

        if b'version-control-tools' not in v:
            continue
        i = v.index(b'version-control-tools')
        vct = v[0:i + len(b'version-control-tools')]
        seenvct.add(vct)

    if len(seenvct) > 1:
        ui.write(MULTIPLE_VCT % cw.path)


def _handleconfigchange(ui, cw):
    # Obtain the old and new content so we can show a diff.
    newbuf = pycompat.bytesio()
    cw.write(newbuf)
    newbuf.seek(0)
    newlines = [pycompat.sysstr(l.rstrip()) for l in newbuf.readlines()]
    oldlines = []
    if os.path.exists(cw.path):
        with open(cw.path, 'rb') as fh:
            oldlines = [pycompat.sysstr(l.rstrip()) for l in fh.readlines()]

    diff = list(difflib.unified_diff(oldlines, newlines,
                                     'hgrc.old', 'hgrc.new',
                                     lineterm=''))

    if len(diff):
        ui.write(b'Your config file needs updating.\n')
        if not ui.promptchoice(b'Would you like to see a diff of the changes first (Yn)? $$ &Yes $$ &No'):
            for line in diff:
                ui.write(b'%s\n' % pycompat.bytestr(line))
            ui.write(b'\n')

        if not ui.promptchoice(b'Write changes to hgrc file (Yn)? $$ &Yes $$ &No'):
            with open(cw.path, 'wb') as fh:
                fh.write(newbuf.getvalue())
        else:
            ui.write(b'config changes not written; we would have written the following:\n')
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
        ui.write(b'Changing permissions of %s\n' % cw.path)
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
        self._random = pycompat.bytestr(uuid.uuid4())

        lines = []

        if os.path.exists(path):
            with open(path, 'rb') as fh:
                for line in fh:
                    # Mercurial has special syntax to include other files.
                    # ConfigObj doesn't recognize it. Normalize on read and
                    # restore on write to preserve it.
                    if line.startswith(b'%include'):
                        line = b'#%s %s' % (self._random, line)

                    if line.startswith(b';'):
                        raise error.Abort(b'semicolon (;) comments in config '
                                          b'files not supported',
                                          hint=b'use # for comments')

                    lines.append(line)

        self.c = ConfigObj(infile=lines, encoding='utf-8',
                           write_empty_values=True, list_values=False)

    def write(self, fh):
        lines = self.c.write()
        for line in lines:
            if line.startswith(b'#%s ' % self._random):
                line = line[2 + len(self._random):]

            fh.write(b'%s\n' % line)
