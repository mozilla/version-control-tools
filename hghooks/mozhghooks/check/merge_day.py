# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os

from mercurial.match import match
from mercurial.hg import repository

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner
)

BANNER = b"""
Merge day push contains unexpected changes.
"""


ALLOWED_FILES = (
    b'.hgtags',
    b'CLOBBER',
    b'browser/config/mozconfigs/',
    b'browser/config/version.txt',
    b'browser/config/version_display.txt',
    b'browser/confvars.sh',
    b'build/mozconfig.common',
    b'config/milestone.txt',
    b'mobile/android/config/mozconfigs/',
    b'services/sync/modules/constants.js',
    b'xpcom/components/Module.h',
    b'mobile/android/config/version-files/beta/version.txt',
    b'mobile/android/config/version-files/beta/version_display.txt',
    b'mobile/android/config/version-files/nightly/version.txt',
    b'mobile/android/config/version-files/nightly/version_display.txt',
    b'mobile/android/config/version-files/release/version.txt',
    b'mobile/android/config/version-files/release/version_display.txt',

)

INVALID_PATH_FOUND = b"""
ffxbld-merge can only push changes to
the following paths:
%s

Illegal paths found:
%s%s
"""


class MergeDayCheck(PreTxnChangegroupCheck):
    """ffxbld-merge user should only be able to push merges"""
    @property
    def name(self):
        return b'merge_day'

    def relevant(self):
        return self.ui.environ[b'USER'] in {b'stage-ffxbld-merge', b'ffxbld-merge'}

    def pre(self, node):
        self._unified = _get_unified_repo(self.ui)

    def check(self, ctx):
        if not self.repo_metadata[b'firefox']:
            print_banner(
                self.ui, b'error',
                b'ffxbld-merge cannot push to non-firefox repository %s' %
                    self.repo_metadata[b'path'],
            )
            return False

        # If this commits has already landed in another tree,
        # it must be part of the merge.
        if ctx.node() in self._unified:
            return True

        if len(ctx.parents()) == 2:
            # A merge should be identical to its first parent.
            try:
                next(ctx.diff(ctx.p1()))
            except StopIteration:
                pass
            else:
                print_banner(
                    self.ui, b'error',
                    b'ffxbld-merge cannot push non-trivial merges.',
                )
                return False

        # For commits that haven't landed in another tree, and aren't merges
        # they can only touch files in the allow list.
        matcher = match(
            ctx.repo().root, b'',
            [b'path:%s' % path for path in ALLOWED_FILES],
        )
        invalid_paths = {
            path for path in ctx.files()
            if not matcher(path)
        }
        if invalid_paths:
            print_banner(
                self.ui, b'error',
                INVALID_PATH_FOUND % (
                    b"\n".join(item for item in sorted(ALLOWED_FILES)),
                    b"\n".join(item for item in sorted(invalid_paths)[:20]),
                    b"\n..." if len(invalid_paths) > 20 else b"",
                ),
            )
            return False

        # Accept
        return True

    def post_check(self):
        return True


def _get_unified_repo(ui):
    repo_root = ui.config(b'mozilla', b'repo_root', b'/repo/hg/mozilla')
    if not repo_root.endswith(b'/'):
        repo_root += b'/'

    return repository(ui, os.path.join(repo_root, b'mozilla-unified'))
