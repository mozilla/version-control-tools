# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this,
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import difflib
import errno
import os
import shutil
import ssl
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

        print(FINISHED)
        return 0

