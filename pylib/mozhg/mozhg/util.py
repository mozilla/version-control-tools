# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import
import importlib

import contextlib
import os
import time

from mercurial.node import short
from mercurial import (
    encoding,
    error,
)

import mozautomation.commitparser as commitparser


def import_module(name):
    """Mercurial's demandimport makes checking for a module's existence tricky.

    As demandimport lazyloads even invalid modules, you cannot use a normal
    `import` catching ImportErrors. Performing the import inside a
    `demandimport.disabled()` block will work, however this will also disable
    lazyloading of dependent modules.

    The correct method is to load with demandimport enabled then query an
    attribute of the method."""
    try:
        module = importlib.import_module(name)
        # __name__ will throw if the module cannot be imported; wrapped in an
        # `if` to avoid "useless statement" warnings.
        if module.__name__:
            return module
    except ImportError:
        return None


FIREFOX_ROOT_NODE = b'8ba995b74e18334ab3707f27e9eb8f4e37ba3d29'
THUNDERBIRD_ROOT_NODE = b'e4f4569d451a5e0d12a6aa33ebd916f979dd8faa'


def is_firefox_repo(repo):
    """Determine if a repository is a Firefox repository."""
    try:
        if len(repo) and repo[0].hex() == FIREFOX_ROOT_NODE:
            return True
    except error.FilteredRepoLookupError:
        pass

    # Backdoor for testing.
    return repo.vfs.exists(b'IS_FIREFOX_REPO')


def is_thunderbird_repo(repo):
    """Determine if a repository is a Thunderbird repository."""
    try:
        if len(repo) and repo[0].hex() == THUNDERBIRD_ROOT_NODE:
            return True
    except error.FilteredRepoLookupError:
        pass

    # Backdoor for testing.
    return repo.vfs.exists(b'IS_THUNDERBIRD_REPO')


def identify_repo(repo):
    """Determine information about a repo instance.

    Returns a dict with the following keys:

    firefox
       Bool indicating if the repo is a Firefox repo.
    firefox_releasing
       Bool if this is a Firefox repo where released Firefoxen could come
       from. These repos have more stringent requirements than a typical
       Firefox repo.
    thunderbird
       Bool indicating if the repo is a Thunderbird repo.
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
    repo_root = repo.ui.config(b'mozilla', b'repo_root', b'/repo/hg/mozilla')
    if not repo_root.endswith(b'/'):
        repo_root += b'/'

    publishing = repo.ui.configbool(b'phases', b'publish')

    d = {
        b'firefox': is_firefox_repo(repo),
        b'thunderbird': is_thunderbird_repo(repo),
        b'publishing': publishing,
    }

    if repo.root.startswith(repo_root):
        d[b'hosted'] = True
        d[b'path'] = repo.root[len(repo_root):]
        d[b'user_repo'] = d[b'path'].startswith(b'users/')

    else:
        d[b'hosted'] = False
        d[b'path'] = repo.root
        d[b'user_repo'] = False

    # We could potentially exclude more Firefox repos from this list. For now,
    # be liberal in what we apply this label to.
    d[b'firefox_releasing'] = (
        d[b'firefox']
        and repo.ui.configbool(b'mozilla', b'firefox_releasing', False)
        and not d[b'user_repo'])

    return d


def repo_owner(repo):
    """Identify the group owner of a repository."""
    # Module not available on Windows. So delay import.
    import grp

    group = repo.vfs.tryread(b'moz-owner').strip()

    if not group:
        gid = os.stat(repo.root).st_gid
        try:
            group = grp.getgrgid(gid).gr_name.encode('utf8')
        except KeyError:
            group = b'<unknown>'

    return group


def get_backoutbynode(ext_name, repo, ctx):
    """Look for changesets that back out this one."""
    # We limit the distance we search for backouts because an exhaustive
    # search could be very intensive. e.g. you load up the root commit
    # on a repository with 200,000 changesets and that commit is never
    # backed out. This finds most backouts because backouts typically happen
    # shortly after a bad commit is introduced.
    thisshort = short(ctx.node())
    count = 0
    searchlimit = repo.ui.configint(ext_name, b'backoutsearchlimit', 100)
    for bctx in repo.set(b'%ld::', [ctx.rev()]):
        count += 1
        if count >= searchlimit:
            break

        backouts = commitparser.parse_backouts(
            encoding.fromlocal(bctx.description()))
        if backouts and thisshort in backouts[0]:
            return bctx.hex()
    return None


class timers(object):
    """Logs times to blackbox logger."""
    def __init__(self, ui, facility, prefix):
        self._ui = ui
        self._facility = facility
        self._prefix = prefix
        self._times = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        for name in sorted(self._times):
            self._ui.log(self._facility,
                         b'%s%s took %.3f seconds\n',
                         self._prefix,
                         name,
                         self._times[name])

    @contextlib.contextmanager
    def timeit(self, name):
        self._times.setdefault(name, 0.0)
        t0 = time.time()

        try:
            yield
        finally:
            self._times[name] += time.time() - t0
