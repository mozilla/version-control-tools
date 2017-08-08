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

UNRELATED_REPO_MESSAGE = '''
*** pushing unrelated repository ***

Changeset %s introduces a new root changeset into this repository. This
almost certainly means you accidentally force pushed to the wrong
repository and/or URL.

Your push is being rejected because this is almost certainly not what you
intended.
'''.lstrip()


class SingleRootCheck(PreTxnChangegroupCheck):
    """Verifies that a repository only has a single root.

    Repositories with multiple roots are typically non-sensical. Without this
    check, `hg push --force` can push an unrelated repo to another one,
    introducing a discrete DAG and making all who use the repo confused.

    In rare conditions, it is desirable to introduce a new root. e.g. when
    merging 2 unrelated repos while preserving history. A facility is provided
    to allow extra roots to exist.
    """
    @property
    def name(self):
        return 'single_root'

    def relevant(self):
        return not self.repo_metadata['user_repo']

    def pre(self):
        self.new_roots = set()

    def check(self, ctx):
        if ctx.rev() != 0 and ctx.p1().node() == nullid:
            self.new_roots.add(ctx.node())

        return True

    def post_check(self):
        if not self.new_roots:
            return True

        # Allow the config to declare allowed new roots.
        #
        # Lists of allowed roots are indexed by the initial rev 0 changeset
        # of the repo. This means different logical repositories have
        # different sets of allowed roots. This also means the allowed roots
        # for a logical repository only has to be declared once (presumably
        # in the global hgrc) for it to work on all clones of that repo.
        #
        # We don't have a global list of allowed roots shared across all repos
        # because it would be possible to push any root in that global set to
        # any repo, completely undermining the hook.
        #
        # We also don't support magic syntax in commit messages to allow new
        # roots because we don't trust users to not abuse this.

        allowed_roots = self.ui.configlist('allowedroots', self.repo[0].hex())
        allowed_roots = set(map(bin, allowed_roots))

        bad_roots = self.new_roots - allowed_roots
        good_roots = self.new_roots & allowed_roots

        for root in sorted(good_roots):
            self.ui.write('(allowing new root %s because it is in the '
                          'whitelist)\n' % short(root))

        if not bad_roots:
            return True

        self.ui.write(UNRELATED_REPO_MESSAGE %
                      ', '.join(sorted(map(short, bad_roots))))
        return False
