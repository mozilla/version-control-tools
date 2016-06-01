# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this,
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import difflib
import errno
import os
import shutil
import ssl
import stat
import sys
import subprocess

from distutils.version import LooseVersion

from configobj import ConfigObjError
from StringIO import StringIO

from mozversioncontrol import get_hg_path, get_hg_version

from .update import MercurialUpdater
from .config import (
    config_file,
    MercurialConfig,
    ParseException,
)

FINISHED = '''
Your Mercurial should now be properly configured and recommended extensions
should be up to date!
'''.strip()

FILE_PERMISSIONS_WARNING = '''
Your hgrc file is currently readable by others.

Sensitive information such as your Bugzilla credentials could be
stolen if others have access to this file/machine.
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


class MercurialSetupWizard(object):
    """Command-line wizard to help users configure Mercurial."""

    def __init__(self, state_dir):
        # We use normpath since Mercurial expects the hgrc to use native path
        # separators, but state_dir uses unix style paths even on Windows.
        self.state_dir = os.path.normpath(state_dir)
        self.ext_dir = os.path.join(self.state_dir, 'mercurial', 'extensions')
        self.vcs_tools_dir = os.path.join(self.state_dir, 'version-control-tools')
        self.updater = MercurialUpdater(state_dir)

    def run(self, config_paths):
        try:
            os.makedirs(self.ext_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        hg = get_hg_path()
        config_path = config_file(config_paths)

        self.updater.update_all()

        hg_version = get_hg_version(hg)

        # Look for and clean up old extensions.
        for ext in {'bzexport', 'qimportbz', 'mqext'}:
            path = os.path.join(self.ext_dir, ext)
            if os.path.exists(path):
                if self._prompt_yn('Would you like to remove the old and no '
                    'longer referenced repository at %s' % path):
                    print('Cleaning up old repository: %s' % path)
                    shutil.rmtree(path)

        # Python + Mercurial didn't have terrific TLS handling until Python
        # 2.7.9 and Mercurial 3.4. For this reason, it was recommended to pin
        # certificates in Mercurial config files. In modern versions of
        # Mercurial, the system CA store is used and old, legacy TLS protocols
        # are disabled. The default connection/security setting should
        # be sufficient and pinning certificates is no longer needed.
        have_modern_ssl = hasattr(ssl, 'SSLContext')
        if hg_version < LooseVersion('3.4') or not have_modern_ssl:
            c.add_mozilla_host_fingerprints()

        # We always update fingerprints if they are present. We /could/ offer to
        # remove fingerprints if running modern Python and Mercurial. But that
        # just adds more UI complexity and isn't worth it.
        c.update_mozilla_host_fingerprints()

        # References to multiple version-control-tools checkouts can confuse
        # version-control-tools, since various Mercurial extensions resolve
        # dependencies via __file__ and repos could reference another copy.
        seen_vct = set()
        for k, v in c.config.get('extensions', {}).items():
            if 'version-control-tools' not in v:
                continue

            i = v.index('version-control-tools')
            vct = v[0:i + len('version-control-tools')]
            seen_vct.add(os.path.realpath(os.path.expanduser(vct)))

        if len(seen_vct) > 1:
            print(MULTIPLE_VCT % c.config_path)

        # At this point the config should be finalized.

        if sys.platform != 'win32':
            # Config file may contain sensitive content, such as passwords.
            # Prompt to remove global permissions.
            mode = os.stat(config_path).st_mode
            if mode & (stat.S_IRWXG | stat.S_IRWXO):
                print(FILE_PERMISSIONS_WARNING)
                if self._prompt_yn('Remove permissions for others to '
                                   'read your hgrc file'):
                    # We don't care about sticky and set UID bits because
                    # this is a regular file.
                    mode = mode & stat.S_IRWXU
                    print('Changing permissions of %s' % config_path)
                    os.chmod(config_path, mode)

        print(FINISHED)
        return 0

    def can_use_extension(self, c, name, path=None):
        # Load extension to hg and search stdout for printed exceptions
        if not path:
            path = os.path.join(self.vcs_tools_dir, 'hgext', name)
        result = subprocess.check_output(['hg',
             '--config', 'extensions.testmodule=%s' % path,
             '--config', 'ui.traceback=true'],
            stderr=subprocess.STDOUT)
        return b"Traceback" not in result

    def prompt_external_extension(self, c, name, prompt_text, path=None):
        # Ask the user if the specified extension should be enabled. Defaults
        # to treating the extension as one in version-control-tools/hgext/
        # in a directory with the same name as the extension and thus also
        # flagging the version-control-tools repo as needing an update.
        if name not in c.extensions:
            if not self.can_use_extension(c, name, path):
                return
            print(name)
            print('=' * len(name))
            print('')
            if not self._prompt_yn(prompt_text):
                print('')
                return
        if not path:
            # We replace the user's home directory with ~ so the
            # config file doesn't depend on the path to the home
            # directory
            path = os.path.join(self.vcs_tools_dir.replace(os.path.expanduser('~'), '~'), 'hgext', name)
        c.activate_extension(name, path)
        print('Activated %s extension.\n' % name)

    def _prompt(self, msg, allow_empty=False):
        print(msg)

        while True:
            response = raw_input().decode('utf-8')

            if response:
                return response

            if allow_empty:
                return None

            print('You must type something!')

    def _prompt_yn(self, msg):
        print('%s? [Y/n]' % msg)

        while True:
            choice = raw_input().lower().strip()

            if not choice:
                return True

            if choice in ('y', 'yes'):
                return True

            if choice in ('n', 'no'):
                return False

            print('Must reply with one of {yes, no, y, n}.')
