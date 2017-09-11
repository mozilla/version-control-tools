# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import


from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)


X_CHANNEL_COMMIT_FOUND = """
You are trying to commit with a message that conflicts with
cross-channel localization.
Please adjust your commit messages to avoid lines starting with
X-Channel-.
"""


class XChannelMessageCheck(PreTxnChangegroupCheck):
    """Prevents X-Channel- commit messages from being committed.

    X-Channel-... is used as meta data in converted commits
    for cross-channel localization, and needs to be prohibited
    from coming in from upstream in all related repositories.
    That's affecting mozilla-central and comm-central at this point.
    """
    @property
    def name(self):
        return 'x_channel_message'

    def relevant(self):
        return self.repo_metadata['firefox']

    def pre(self):
        pass

    def check(self, ctx):
        if not any(line.startswith('X-Channel-')
                   for line in ctx.description().splitlines()):
            return True

        print_banner(self.ui, 'error', X_CHANNEL_COMMIT_FOUND)
        return False

    def post_check(self):
        return True
