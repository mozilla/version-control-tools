# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os

from mercurial.match import match
from mercurial.hg import repository

from ..checks import PreTxnChangegroupCheck, print_banner

BANNER = b"""
Merge day push contains unexpected changes.
"""

ALLOWED_FILES = {
    b"firefox": (
        b".hgtags",
        b"CLOBBER",
        b"browser/config/mozconfigs/",
        b"browser/config/version.txt",
        b"browser/config/version_display.txt",
        b"browser/locales/l10n-changesets.json",
        b"build/defines.sh",
        b"build/mozconfig.common",
        b"config/milestone.txt",
        b"services/sync/modules/constants.js",
        b"xpcom/components/Module.h",
    ),
    b"thunderbird": (
        b".hgtags",
        b".gecko_rev.yml",
        b"mail/config/mozconfigs/",
        b"mail/config/version.txt",
        b"mail/config/version_display.txt",
        b"mail/locales/l10n-changesets.json",
        b"suite/config/version.txt",
        b"suite/config/version_display.txt",
    ),
}

FF_MERGE_USER = b"ffxbld-merge"
FF_STAGE_USER = b"stage-ffxbld-merge"
TB_MERGE_USER = b"tbbld-merge"
TB_STAGE_USER = b"stage-tbbld-merge"

ALL_MERGE_USERS = {FF_MERGE_USER, FF_STAGE_USER, TB_MERGE_USER, TB_STAGE_USER}

UNIFIED_REPOS = {
    b"firefox": b"mozilla-unified",
    b"thunderbird": b"comm-central",
}


INVALID_PATH_FOUND = b"""
%s can only push changes to
the following paths:
%s

Illegal paths found:
%s%s
"""


class MergeDayCheck(PreTxnChangegroupCheck):
    """merge user should only be able to push merges"""

    @property
    def name(self):
        return b"merge_day"

    @property
    def current_user(self):
        return self.ui.environ[b"USER"]

    @property
    def relevant_repos(self):
        if self.current_user in {FF_MERGE_USER, FF_STAGE_USER}:
            return b"firefox"
        elif self.current_user in {TB_MERGE_USER, TB_STAGE_USER}:
            return b"thunderbird"

    def allowed_files(self):
        return ALLOWED_FILES[self.relevant_repos]

    def relevant(self):
        return self.current_user in ALL_MERGE_USERS

    def pre(self, node):
        self._unified = _get_unified_repo(self.ui, self.relevant_repos)

    def check(self, ctx):
        if not self.repo_metadata[self.relevant_repos]:
            print_banner(
                self.ui,
                b"error",
                b"%s cannot push to non-%s repository %s"
                % (self.current_user, self.relevant_repos, self.repo_metadata[b"path"]),
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
                    self.ui,
                    b"error",
                    b"%s cannot push non-trivial merges." % self.current_user,
                )
                return False

        # For commits that haven't landed in another tree, and aren't merges
        # they can only touch files in the allow list.
        matcher = match(
            ctx.repo().root,
            b"",
            [b"path:%s" % path for path in self.allowed_files()],
        )
        invalid_paths = {path for path in ctx.files() if not matcher(path)}
        if invalid_paths:
            print_banner(
                self.ui,
                b"error",
                INVALID_PATH_FOUND
                % (
                    self.current_user,
                    b"\n".join(item for item in sorted(self.allowed_files())),
                    b"\n".join(item for item in sorted(invalid_paths)[:20]),
                    b"\n..." if len(invalid_paths) > 20 else b"",
                ),
            )
            return False

        # Accept
        return True

    def post_check(self):
        return True


def _get_unified_repo(ui, repos):
    repo_root = ui.config(b"mozilla", b"repo_root", b"/repo/hg/mozilla")
    if not repo_root.endswith(b"/"):
        repo_root += b"/"

    unified_name = UNIFIED_REPOS[repos]
    return repository(ui, os.path.join(repo_root, unified_name))
