# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""
run clang-format as part of the commit

For this, we override the commit command, run:
./mach clang-format -p <file>
and call the mercurial commit function
"""

import os
import subprocess

from mercurial import (
    extensions,
    localrepo,
    match
)

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.util import is_firefox_repo


testedwith = '4.4 4.5 4.6 4.7 4.8 4.9'
minimumhgversion = '4.4'


def wrappedcommit(orig, repo, *args, **kwargs):
    try:
        path_matcher = args[3]
    except IndexError:
        # In a rebase for example
        return orig(repo, *args, **kwargs)

    # In case hg changes the position of the arg
    # path_matcher will be empty in case of histedit
    assert isinstance(path_matcher, match.basematcher) or path_matcher is None

    try:
        lock = repo.wlock()
        status = repo.status(match=path_matcher)
        changed_files = sorted(status.modified + status.added)
        mach_path = os.path.join(repo.root, 'mach')

        if not is_firefox_repo(repo) or not changed_files:
            # this isn't a firefox repo, don't run clang-format
            # as it is fx specific
            # OR we don't modify any files
            lock.release()
            return orig(repo, *args, **kwargs)

        arguments = ['clang-format', '-p'] + changed_files
        if os.name == 'nt':
            clang_format_cmd = ['sh', 'mach'] + arguments
        else:
            clang_format_cmd = [mach_path] + arguments
        subprocess.call(clang_format_cmd)
    except Exception as e:
        repo.ui.warn('Exception %s\n' % str(e))

    finally:
        lock.release()
        return orig(repo, *args, **kwargs)


def extsetup(ui):
    extensions.wrapfunction(localrepo.localrepository, 'commit', wrappedcommit)
