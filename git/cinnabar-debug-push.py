#!/usr/bin/env python2.7
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This is a low-level script for pushing via git-cinnabar and obtaining the
# results as structured output.

from __future__ import absolute_import, print_function, unicode_literals

import argparse
from binascii import hexlify
import json
import sys

import cinnabar.util
try:
    from cinnabar.hg.repo import (
        get_ui,
        push,
    )
except ImportError:
    from cinnabar.hg import (
        get_ui,
        push,
    )
try:
    from cinnabar.hg.bundle import PushStore
except ImportError:
    from cinnabar.bundle import PushStore

try:
    from cinnabar.util import init_logging
except ImportError:
    def init_logging(): pass

try:
    from cinnabar.hg.repo import (
        get_repo,
        passwordmgr,
        Remote,
    )
except ImportError:
    try:
        from cinnabar.hg import (
            get_repo,
            passwordmgr,
            Remote,
        )
    except ImportError:
        passwordmgr = False

# Disable progress printing otherwise output can be a bit wonky.
cinnabar.util.progress = False


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='URL of Mercurial repo to push to')
    parser.add_argument('commit', help='Git commit to push')
    parser.add_argument('--config-file', action='append',
                        help='Extra Mercurial config file to load')

    args = parser.parse_args(args)

    url = args.url
    commit = args.commit

    init_logging()

    if passwordmgr:
        repo = get_repo(Remote('hg::%s' % url, url))
    else:
        from mercurial import hg

        ui = get_ui()

        for p in args.config_file or []:
            ui.readconfig(p, trust=True)

        repo = hg.peer(ui, {}, url)

    heads = (hexlify(h) for h in repo.heads())
    store = PushStore()
    try:
        pushed = push(repo, store, {commit: (None, False)}, heads, ())
    except Exception as e:
        # This is a common error. So rather than display the entire stack to
        # the user, exit with a well-defined exit code so the caller can
        # display a nice error message.
        if any(arg.startswith('Pushing merges is not supported yet')
               for arg in getattr(e, 'args', ())[:1]):
            return 127
        raise

    commits = []
    if pushed:
        for commit in pushed.iternodes():
            changeset = store.hg_changeset(commit)
            ref = store.changeset_ref(changeset)
            new_data = type(ref) != str

            commits.append([commit, changeset, new_data])

    # By now, cinnabar or its subprocesses should not be writing anything to
    # either stdout or stderr. Ensure stderr is flushed for _this_ process,
    # since git-mozreview uses the same file descriptor for both stdout and
    # stderr, and we want to try to avoid mixed output.
    sys.stderr.flush()
    for commit, changeset, new_data in commits:
        print('>result>', commit, changeset, new_data)
    sys.stdout.flush()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
