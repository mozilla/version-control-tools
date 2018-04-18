# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import


from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)


SYMLINK_FOUND = """
{node} adds or modifies the following symlinks:

  {symlinks}

Symlinks aren't allowed in this repo. Convert these paths to regular
files and try your push again.
"""


class PreventSymlinksCheck(PreTxnChangegroupCheck):
    """Prevents symlinks from being committed.

    Symlinks don't work on all platforms. While Mercurial knows how to check out
    a symlink on platforms that don't support symlinks, the behavior is wonky.

    We want cross-platform consistency with regards to repository behavior. So
    our policy is to ban symlinks on most repos.
    """

    @property
    def name(self):
        return 'prevent_symlinks'

    def relevant(self):
        return not self.repo_metadata['user_repo']

    def pre(self, node):
        pass

    def check(self, ctx):
        manifest = ctx.manifest()
        links = []

        for f in ctx.files():
            if f not in manifest:
                continue

            if manifest.flags(f) == 'l':
                links.append(f)

        if not links:
            return True

        print_banner(self.ui, 'error', SYMLINK_FOUND.format(
            node=ctx.hex()[0:12],
            symlinks='\n  '.join(links)))
        return False

    def post_check(self):
        return True
