# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os


def find_hg_repos(path):
    '''Finds all Mercurial repositories contained in the
    directory at `path`.'''
    for root, dirs, files in os.walk(path):
        for d in sorted(dirs):
            if d == '.hg':
                yield root

        dirs[:] = [d for d in sorted(dirs) if d != '.hg']
