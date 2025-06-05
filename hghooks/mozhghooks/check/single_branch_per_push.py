# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial.node import (
    bin,
    nullid,
    short,
)

from ..checks import (
    PreTxnChangegroupCheck,
)

MULTIPLE_BRANCHES_MESSAGE = b"""
*** pushing multiple branches ***

This push includes changesets in several branches: %s

Your push is being rejected because this is almost certainly not what you
intended.
""".lstrip()


class SingleBranchCheck(PreTxnChangegroupCheck):
    """Verifies that a push only touches a single branch

    Pushlog consumers assume that changesets in a push are a linear unit.
    """

    @property
    def name(self):
        return b"single_branch"

    def relevant(self):
        return not self.repo_metadata[b"user_repo"]

    def pre(self, node):
        self.branches = set()

    def check(self, ctx):
        self.branches.add(ctx.branch())

        return True

    def post_check(self):
        if len(self.branches) <= 1:
            return True

        self.ui.write(
            MULTIPLE_BRANCHES_MESSAGE % b", ".join(sorted(self.branches))
        )
        return False
