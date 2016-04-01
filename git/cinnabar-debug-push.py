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
from cinnabar.hg import (
    get_ui,
    push,
)
from cinnabar.bundle import (
    PushStore,
)

from mercurial import (
    hg,
)

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

    ui = get_ui()

    for p in args.config_file or []:
        ui.readconfig(p, trust=True)

    repo = hg.peer(ui, {}, url)

    # Buffer output.
    repo.ui.pushbuffer(error=True, subproc=True)

    heads = (hexlify(h) for h in repo.heads())
    store = PushStore()
    pushed = push(repo, store, {commit: (None, False)}, heads, ())

    push_output = repo.ui.popbuffer()

    commits = []
    if pushed:
        for commit in pushed.iternodes():
            changeset = store.hg_changeset(commit)
            ref = store.changeset_ref(changeset)
            new_data = type(ref) != str

            commits.append([commit, changeset, new_data])

    print(json.dumps({
        'output': push_output,
        'commits': commits,
    }, sort_keys=True, encoding='utf-8', indent=2))

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print(json.dumps({
            'error': str(e),
        }))
        sys.exit(0)
