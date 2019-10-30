# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os
import re

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

allowed_paths = re.compile(b"testing/web-platform/(?:moz\.build|meta/.*|tests/.*)$")

INVALID_PATH_FOUND = b"""
wptsync@mozilla.com can only make changes to
the following paths on %s:
testing/web-platform/moz.build
testing/web-platform/meta
testing/web-platform/tests

Illegal paths found:
%s%s
"""

ILLEGAL_REPO = b"""
wptsync@mozilla.com cannot push to %s
"""


class WPTSyncCheck(PreTxnChangegroupCheck):
    """
    Prevents changes to files outside of testing/web-platform
    subdirectories for account wptsync@mozilla.com, and only allows
    pushes to autoland from among production repos.

    This account is used by a two-way repository sync between
    mozilla-central and w3c/web-platform-tests on GitHub.
    """
    @property
    def name(self):
        return b'wptsync_check'

    def relevant(self):
        return self.ui.environ[b'USER'] == b'wptsync@mozilla.com'

    def pre(self, node):
        pass

    def check(self, ctx):
        success = False
        if self.repo_metadata[b'path'] == b'try':
            success = True
        elif self.repo_metadata[b'path'] == b'integration/autoland':
            invalid_paths = [path for path in ctx.files() if not allowed_paths.match(path)]
            if not invalid_paths:
                success = True
            else:
                invalid_paths = set(invalid_paths)
                print_banner(self.ui, b'error', INVALID_PATH_FOUND % (
                    self.repo_metadata[b'path'],
                    b"\n".join(item for item in sorted(invalid_paths)[:20]),
                    b"\n..." if len(invalid_paths) > 20 else b""
                ))
        else:
            print_banner(self.ui, b'error',
                         ILLEGAL_REPO % self.repo_metadata[b'path'])
        return success

    def post_check(self):
        return True
