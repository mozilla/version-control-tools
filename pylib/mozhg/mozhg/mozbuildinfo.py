# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import mercurial.error as error

import mozbuild.frontend.context as mbcontext
import mozbuild.frontend.reader as reader
import mozpack.hg as mozpackhg


def filesinfo(repo, ctx, paths=None):
    """Obtain mozbuild files info for a changectx and list of files.

    If the list of files is not specified, the files changed by the changeset
    are used.

    Returns a dict containing moz.build derived file info. The dict has a
    ``files`` key which contains a dict of file path to dict of metadata.
    The ``aggregate`` key contains a dict of additional, aggregate metadata
    that applies to all requests paths.

    WARNING: RISK OF UNTRUSTED CODE EXECUTION.

    moz.build files are Python files and evaluating them requires executing
    Python code. While moz.build files are sandboxed, Python sandboxes aren't
    sufficient security sandboxes. A specially crafted moz.build file could
    almost certainly escape the sandbox and gain access to a) the calling
    Python's frames and variables b) the ability to import arbitrary Python
    modules c) access to the filesystem and the ability to execute any program
    therein. THIS FUNCTION SHOULD ONLY BE CALLED BY PRIVILEGE LIMITED USERS
    AND PROCESSES.
    """

    # This method only works if the repository has a moz.build file in the
    # root directory, as the moz.build file info reading mode requires one.
    if 'moz.build' not in ctx:
        return None

    paths = paths or ctx.files()
    if not paths:
        return None

    finder = mozpackhg.MercurialNativeRevisionFinder(repo, ctx.rev(),
            recognize_repo_paths=True)

    config = reader.EmptyConfig(repo.root)
    br = reader.BuildReader(config, finder=finder)
    info = br.files_info(paths)

    return {
        'files': {p: f.asdict() for p, f in info.items()},
        'aggregate': mbcontext.Files.aggregate(info),
    }
