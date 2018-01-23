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
testing/web-platform/moz.build
testing/web-platform/meta
testing/web-platform/tests

Illegal paths found:
{}{}
"""


class WPTSyncCheck(PreTxnChangegroupCheck):
    """
    Prevents changes to files outside of testing/web-platform
    subdirectories for account wptsync@mozilla.com.

    This account is used by a two-way repository sync between
    mozilla-central and w3c/web-platform-tests on GitHub.
    """
    @property
    def name(self):
        return 'wptsync_check'

    def relevant(self):
        return self.repo_metadata['firefox_releasing']

    def pre(self):
        pass

    def check(self, ctx):
        success = True
        if os.environ['USER'] == 'wptsync@mozilla.com':
            invalid_paths = [path for path in ctx.files()
                             if not allowed_paths.match(path)]

            if invalid_paths:
                invalid_paths = set(invalid_paths)
                print_banner(self.ui, 'error', INVALID_PATH_FOUND.format(
                    "\n".join(item for item in sorted(invalid_paths)[:20]),
                    "\n..." if len(invalid_paths) > 20 else ""
                ))
                success = False
        return success

    def post_check(self):
        return True
