# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial import (
    error,
)


FIREFOX_ROOT_NODE = '8ba995b74e18334ab3707f27e9eb8f4e37ba3d29'
THUNDERBIRD_ROOT_NODE = 'e4f4569d451a5e0d12a6aa33ebd916f979dd8faa'


def is_firefox_repo(repo):
    """Determine if a repository is a Firefox repository."""
    try:
        if len(repo) and repo[0].hex() == FIREFOX_ROOT_NODE:
            return True
    except error.FilteredRepoLookupError:
        pass

    # Backdoor for testing.
    return repo.vfs.exists('IS_FIREFOX_REPO')


def is_thunderbird_repo(repo):
    """Determine if a repository is a Thunderbird repository."""
    try:
        if len(repo) and repo[0].hex() == THUNDERBIRD_ROOT_NODE:
            return True
    except error.FilteredRepoLookupError:
        pass

    # Backdoor for testing.
    return repo.vfs.exists('IS_THUNDERBIRD_REPO')


def identify_repo(repo):
    """Determine information about a repo instance.

    Returns a dict with the following keys:

    firefox
       Bool indicating if the repo is a Firefox repo.
    firefox_releasing
       Bool if this is a Firefox repo where released Firefoxen could come
       from. These repos have more stringent requirements than a typical
       Firefox repo.
    hosted
       Bool indicating if the repo is hosted. (In a path used by servers.)
    user_repo
       Bool indicating if the repo is a user repository.
    publishing
       Bool indicating if hte repo is publishing.
    path
       Path to the repository. If a hosted repo, this will be the repo path
       minus the hosting prefix. Else, this will be the repo's path.
    """
    repo_root = repo.ui.config('mozilla', 'repo_root', '/repo/hg/mozilla')
    if not repo_root.endswith('/'):
        repo_root += '/'

    d = {
        'firefox': is_firefox_repo(repo),
        'thunderbird': is_thunderbird_repo(repo),
        'publishing': repo.ui.configbool('phases', 'publish', True),
    }

    if repo.root.startswith(repo_root):
        d['hosted'] = True
        d['path'] = repo.root[len(repo_root):]
        d['user_repo'] = d['path'].startswith('users/')

    else:
        d['hosted'] = False
        d['path'] = repo.root
        d['user_repo'] = False

    # We could potentially exclude more Firefox repos from this list. For now,
    # be liberal in what we apply this label to.
    d['firefox_releasing'] = (
        d['firefox']
        and d['publishing']
        and not d['user_repo'])

    return d
