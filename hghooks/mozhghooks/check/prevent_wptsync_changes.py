# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os
import re

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

allowed_paths = re.compile("testing/web-platform/(?:moz\.build|meta/.*|tests/.*)$")

INVALID_PATH_FOUND = """
wptsync@mozilla.com can only make changes to
the following paths on {}:
testing/web-platform/moz.build
testing/web-platform/meta
testing/web-platform/tests

Illegal paths found:
{}{}
"""

ILLEGAL_REPO = """
wptsync@mozilla.com cannot push to {}
"""


class WPTSyncCheck(PreTxnChangegroupCheck):
    """
    Prevents changes to files outside of testing/web-platform
    subdirectories for account wptsync@mozilla.com, and only allows
    pushes to mozilla-inbound from among production repos.

    This account is used by a two-way repository sync between
    mozilla-central and w3c/web-platform-tests on GitHub.
    """
    @property
    def name(self):
        return 'wptsync_check'

    def relevant(self):
        return os.environ['USER'] == 'wptsync@mozilla.com'

    def pre(self, node):
        pass

    def check(self, ctx):
        success = False
        if self.repo_metadata['path'] == 'try':
            success = True
        elif self.repo_metadata['path'] == 'integration/mozilla-inbound':
            invalid_paths = [path for path in ctx.files() if not allowed_paths.match(path)]
            if not invalid_paths:
                success = True
            else:
                invalid_paths = set(invalid_paths)
                print_banner(self.ui, 'error', INVALID_PATH_FOUND.format(
                    self.repo_metadata['path'],
                    "\n".join(item for item in sorted(invalid_paths)[:20]),
                    "\n..." if len(invalid_paths) > 20 else ""
                ))
        else:
            print_banner(self.ui, 'error',
                         ILLEGAL_REPO.format(self.repo_metadata['path']))
        return success

    def post_check(self):
        return True
