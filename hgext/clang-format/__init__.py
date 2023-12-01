# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""
run clang-format as part of the commit

For this, we override the commit command, run:
./mach clang-format -p <file>
and call the mercurial commit function
"""

import os
import shutil
import subprocess

from mercurial import (
    cmdutil,
    error,
    extensions,
    localrepo,
    match,
    pycompat,
    scmutil,
)

OUR_DIR = os.path.dirname(__file__)
with open(os.path.join(OUR_DIR, "..", "bootstrap.py")) as f:
    exec(f.read())

from mozhg.util import is_firefox_repo


testedwith = b"4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.2 5.3"
minimumhgversion = b"4.4"
buglink = b"https://bugzilla.mozilla.org/enter_bug.cgi?product=Firefox%20Build%20System&component=Lint%20and%20Formatting"  # noqa: E501


def find_python():
    for python_variant in ("py", "python3", "python"):
        if shutil.which(python_variant):
            return python_variant.encode("utf-8")

    raise error.Abort(b"Could not find a suitable Python to run `mach`!")


def call_clang_format(repo, changed_files):
    """Call `./mach clang-format` on the changed files"""
    # We have also a copy of this list in:
    # python/mozbuild/mozbuild/mach_commands.py
    # tools/lint/hooks_clang_format.py
    # release-services/src/staticanalysis/bot/static_analysis_bot/config.py
    # Too heavy to import the full class just for this variable
    extensions = (b".cpp", b".c", b".cc", b".h", b".m", b".mm")
    path_list = []
    for filename in sorted(changed_files):
        # Ignore files unsupported in clang-format
        if filename.endswith(extensions):
            path_list.append(filename)

    if not path_list:
        # No files have been touched
        return

    clang_format_cmd = [
        find_python(),
        os.path.join(repo.root, b"mach"),
        b"clang-format",
        b"-p",
    ] + path_list

    # Set `PYTHONIOENCODING` since `hg.exe` will detect `cp1252` as the encoding
    # and pass it as the encoding to `mach` via the environment.
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    subprocess.call(clang_format_cmd, env=env)


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
            call_clang_format(repo, changed_files)

    except Exception as e:
        repo.ui.warn(b"Exception %s\n" % pycompat.bytestr(str(e)))

    finally:
        lock.release()
        return orig(repo, *args, **kwargs)


def wrappedamend(orig, ui, repo, old, extra, pats, opts):
    """Wraps cmdutil.amend to run clang-format during `hg commit --amend`"""
    wctx = repo[None]
    matcher = scmutil.match(wctx, pats, opts)
    filestoamend = [f for f in wctx.files() if matcher(f)]

    if not filestoamend:
        return orig(ui, repo, old, extra, pats, opts)

    try:
        with repo.wlock():
            call_clang_format(repo, filestoamend)

    except Exception as e:
        repo.ui.warn(b"Exception %s\n" % pycompat.bytestr(str(e)))

    return orig(ui, repo, old, extra, pats, opts)


def reposetup(ui, repo):
    # Avoid setup altogether if `moz-phab` is executing hg,
    # or the repository is not a Firefox derivative,
    # or the repo is not local
    if not repo.local() or "MOZPHAB" in os.environ or not is_firefox_repo(repo):
        return

    extensions.wrapfunction(localrepo.localrepository, "commit", wrappedcommit)
    extensions.wrapfunction(cmdutil, "amend", wrappedamend)
