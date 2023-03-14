# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

CROSSREPO_PUSH_DETECTED = b"""
Push contains commits locked to another repo.

Please ensure there are no commits containing REPO-%s in the title.
This repo will only accept such commits containing REPO-%s.
"""

BAD_FORMATTING_SLASH_DETECTED = b"""
Push contains commits intended to be locked to %s but
the repo name is badly formatted. '/' is not allowed.

This repo will only accept commits containing REPO-%s in the title.
"""

UNRESTRICTED_REPOS = [b"try"]


class RepoLockedCheck(PreTxnChangegroupCheck):
    """
    Prevents commits locked to a certain repo from being pushed to another.

    A commit is locked to a repo X by having REPO-X in the title.
    """

    @property
    def name(self):
        return b"repolocked_check"

    def relevant(self):
        return self.repo_metadata[b"path"] not in UNRESTRICTED_REPOS

    def pre(self, node):
        pass

    def check(self, ctx):
        repo = self.repo_metadata[b"path"].split(b"/")[-1]
        title = ctx.description().splitlines()[0]
        locked_to_repos = [
            word.split(b"REPO-", 1)[1] for word in title.split(b" ") if b"REPO-" in word
        ]
        bad = next((lr for lr in locked_to_repos if b"/" in lr), None)
        if bad:
            print_banner(self.ui, b"error", BAD_FORMATTING_SLASH_DETECTED % (bad, repo))
            return False
        if locked_to_repos and not any(lr == repo for lr in locked_to_repos):
            bad = next(lr for lr in locked_to_repos if lr != repo)
            print_banner(self.ui, b"error", CROSSREPO_PUSH_DETECTED % (bad, repo))
            return False
        return True

    def post_check(self):
        return True
