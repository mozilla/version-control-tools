#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Find Mercurial repositories under a specified path."""

import os
import sys

def find_hg_repos(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            if d == '.hg':
                yield root

        dirs[:] = [d for d in dirs if d != '.hg']

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('usage: %s dir0 [dir1] ...')
        sys.exit(1)

    for d in sys.argv[1:]:
        for path in find_hg_repos(d):
            print(path)
