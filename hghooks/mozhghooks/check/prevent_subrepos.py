# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import


from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)


SUBREPO_NOT_ALLOWED = """
{node} contains subrepositories.

Subrepositories are not allowed on this repository.

Please remove .hgsub and/or .hgsubstate files from the repository and try your
push again.
"""


class PreventSubReposCheck(PreTxnChangegroupCheck):
    """Prevents sub-repos from being committed.

    Sub-repos are a power user feature. They make it difficult to convert repos
    to and from Git. We also tend to prefer vendoring into a repo instead of
    creating a "symlink" to another repo.

    This check prevents the introduction of sub-repos on incoming changesets
    for non-user repos. For user repos, it prints a non-fatal warning
    discouraging their use.
    """
    @property
    def name(self):
        return 'prevent_subrepos'

    def relevant(self):
        return True

    def pre(self):
        self.done = False

    def check(self, ctx):
        # Since the check can be non-fatal and since it requires a manifest
        # (which can be expensive to obtain), no-op if there is no work to do.
        if self.done:
            return True

        if '.hgsub' not in ctx and '.hgsubstate' not in ctx:
            return True

        self.done = True

        print_banner(self.ui, 'error', SUBREPO_NOT_ALLOWED.format(
            node=ctx.hex()[0:12]))
        return False

    def post_check(self):
        return True
