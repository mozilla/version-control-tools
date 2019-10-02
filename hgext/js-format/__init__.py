# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""
run eslint and prettier as part of the commit

For this, we override the commit command, run:
./mach eslint --fix <file>
and call the mercurial commit function
"""

import os
import subprocess

from mercurial import (
    cmdutil,
    extensions,
    localrepo,
    match,
    scmutil,
)

OUR_DIR = os.path.dirname(__file__)
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

from mozhg.util import is_firefox_repo


testedwith = '4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1'
minimumhgversion = '4.4'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Firefox%20Build%20System&component=Lint%20and%20Formatting'  # noqa: E501


def call_js_format(repo, changed_files):
    '''Call `./mach eslint --fix` on the changed files'''
    extensions = (".js", ".jsx", ".jsm")
    path_list = []
    for filename in sorted(changed_files):
        # Ignore files unsupported in eslint and prettier
        if filename.endswith(extensions):
            path_list.append(filename)

    if not path_list:
        # No files have been touched
        return

    mach_path = os.path.join(repo.root, 'mach')
    arguments = ['eslint', '--fix'] + path_list
    if os.name == 'nt':
        js_format_cmd = ['sh', 'mach'] + arguments
    else:
        js_format_cmd = [mach_path] + arguments
    subprocess.call(js_format_cmd)


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

        if changed_files:
            call_js_format(repo, changed_files)

    except Exception as e:
        repo.ui.warn('Exception %s\n' % str(e))

    finally:
        lock.release()
        return orig(repo, *args, **kwargs)


def wrappedamend(orig, ui, repo, old, extra, pats, opts):
    '''Wraps cmdutil.amend to run eslint and prettier during `hg commit --amend`'''
    wctx = repo[None]
    matcher = scmutil.match(wctx, pats, opts)
    filestoamend = [f for f in wctx.files() if matcher(f)]

    if not filestoamend:
        return orig(ui, repo, old, extra, pats, opts)

    try:
        with repo.wlock():
            call_js_format(repo, filestoamend)

    except Exception as e:
        repo.ui.warn('Exception %s\n' % str(e))

    return orig(ui, repo, old, extra, pats, opts)


def reposetup(ui, repo):
    # Avoid setup altogether if `moz-phab` is executing hg,
    # or the repository is not a Firefox derivative,
    # or the repo is not local
    if not repo.local() or 'MOZPHAB' in os.environ or not is_firefox_repo(repo):
        return

    extensions.wrapfunction(localrepo.localrepository, 'commit', wrappedcommit)
    extensions.wrapfunction(cmdutil, 'amend', wrappedamend)
