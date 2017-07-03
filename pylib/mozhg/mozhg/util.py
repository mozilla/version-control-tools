# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial import (
    error,
)


FIREFOX_ROOT_NODE = '8ba995b74e18334ab3707f27e9eb8f4e37ba3d29'


def is_firefox_repo(repo):
    """Determine if a repository is a Firefox repository."""
    try:
        if len(repo) and repo[0].hex() == FIREFOX_ROOT_NODE:
            return True
    except error.FilteredRepoLookupError:
        pass

    # Backdoor for testing.
    return repo.vfs.exists('IS_FIREFOX_REPO')
