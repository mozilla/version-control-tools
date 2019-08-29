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


def call_clang_format(repo, changed_files):
    '''Call `./mach clang-format` on the changed files'''
    # We have also a copy of this list in:
    # python/mozbuild/mozbuild/mach_commands.py
    # tools/lint/hooks_clang_format.py
    # release-services/src/staticanalysis/bot/static_analysis_bot/config.py
    # Too heavy to import the full class just for this variable
    extensions = (".cpp", ".c", ".cc", ".h", ".m", ".mm")
    path_list = []
    for filename in sorted(changed_files):
        # Ignore files unsupported in clang-format
        if filename.endswith(extensions):
            path_list.append(filename)

    if not path_list:
        # No files have been touched
        return

    mach_path = os.path.join(repo.root, 'mach')
    arguments = ['clang-format', '-p'] + path_list
    if os.name == 'nt':
        clang_format_cmd = ['sh', 'mach'] + arguments
    else:
        clang_format_cmd = [mach_path] + arguments
    subprocess.call(clang_format_cmd)


def wrappedcommit(orig, repo, *args, **kwargs):
    try:
        path_matcher = args[3]
    except IndexError:
        # In a rebase for example
        return orig(repo, *args, **kwargs)

    if 'MOZPHAB' in os.environ:
        # We are called by the moz-phab process
        # We don't want to reformat the commit as they have
        # been reformatted by the initial commit
        return orig(repo, *args, **kwargs)

    # In case hg changes the position of the arg
    # path_matcher will be empty in case of histedit
    assert isinstance(path_matcher, match.basematcher) or path_matcher is None

    try:
        lock = repo.wlock()
        status = repo.status(match=path_matcher)
        changed_files = sorted(status.modified + status.added)

        if not is_firefox_repo(repo) or not changed_files:
            # this isn't a firefox repo, don't run clang-format
            # as it is fx specific
            # OR we don't modify any files
            lock.release()
            return orig(repo, *args, **kwargs)

        call_clang_format(repo, changed_files)

    except Exception as e:
        repo.ui.warn('Exception %s\n' % str(e))

    finally:
        lock.release()
        return orig(repo, *args, **kwargs)


def wrappedamend(orig, ui, repo, old, extra, pats, opts):
    '''Wraps cmdutil.amend to run clang-format during `hg commit --amend`'''

    if 'MOZPHAB' in os.environ:
        # We are called by the moz-phab process
        # We don't want to reformat the commit as they have
        # been reformatted by the initial commit
        return orig(ui, repo, old, extra, pats, opts)

    wctx = repo[None]
    matcher = scmutil.match(wctx, pats, opts)
    filestoamend = [f for f in wctx.files() if matcher(f)]

    if not is_firefox_repo(repo) or not filestoamend:
        return orig(ui, repo, old, extra, pats, opts)

    try:
        with repo.wlock():
            call_clang_format(repo, filestoamend)

    except Exception as e:
        repo.ui.warn('Exception %s\n' % str(e))

    return orig(ui, repo, old, extra, pats, opts)


def extsetup(ui):
    extensions.wrapfunction(localrepo.localrepository, 'commit', wrappedcommit)
    extensions.wrapfunction(cmdutil, 'amend', wrappedamend)
