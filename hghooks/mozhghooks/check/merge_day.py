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

BANNER = """
Merge day push contains unexpected changes.
"""


ALLOWED_FILES = (
    '.hgtags',
    'CLOBBER',
    'browser/config/mozconfigs/',
    'browser/config/version.txt',
    'browser/config/version_display.txt',
    'browser/confvars.sh',
    'build/mozconfig.common',
    'config/milestone.txt',
    'mobile/android/config/mozconfigs/',
    'services/sync/modules/constants.js',
    'xpcom/components/Module.h',
)

INVALID_PATH_FOUND = """
ffxbld-merge can only push changes to
the following paths:
{}

Illegal paths found:
{}{}
"""


class MergeDayCheck(PreTxnChangegroupCheck):
    """ffxbld-merge user should only be able to push merges"""
    @property
    def name(self):
        return 'merge_day'

    def relevant(self):
        return os.environ['USER'] in ('stage-ffxbld-merge', 'ffxbld-merge')

    def pre(self, node):
        pass

    def check(self, ctx):
        if not self.repo_metadata['firefox']:
            print_banner(
                self.ui, 'error',
                'ffxbld-merge cannot push to non-firefox repository {}'.format(
                    self.repo_metadata['path']),
            )
            return False

        unified = _get_unified_repo(ctx.repo().ui)

        # If this commits has already landed in another tree,
        # it must be part of the merge.
        if ctx.node() in unified:
            return True

        if len(ctx.parents()) == 2:
            # A merge should be identical to its first parent.
            try:
                next(ctx.diff(ctx.p1()))
            except StopIteration:
                pass
            else:
                print_banner(
                    self.ui, 'error',
                    'ffxbld-merge cannot push non-trivial merges.',
                )
                return False

        # For commits that haven't landed in another tree, and aren't merges
        # they can only touch files in the allow list.
        matcher = match(
            ctx.repo().root, '',
            ['path:{}'.format(path) for path in ALLOWED_FILES],
        )
        invalid_paths = {
            path for path in ctx.files()
            if not matcher(path)
        }
        if invalid_paths:
            print_banner(
                self.ui, 'error',
                INVALID_PATH_FOUND.format(
                    "\n".join(item for item in sorted(ALLOWED_FILES)),
                    "\n".join(item for item in sorted(invalid_paths)[:20]),
                    "\n..." if len(invalid_paths) > 20 else "",
                ),
            )
            return False

        # Accept
        return True

    def post_check(self):
        return True


def _get_unified_repo(ui):
    repo_root = ui.config('mozilla', 'repo_root', '/repo/hg/mozilla')
    if not repo_root.endswith('/'):
        repo_root += '/'

    return repository(ui, os.path.join(repo_root, 'mozilla-unified'))
