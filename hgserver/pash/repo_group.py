#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function

import hg_helper
import sys


def repo_owner(repo):
    if not repo:
        print("Need a repository to check")
        sys.exit(1)

    repo_dir = hg_helper.DOC_ROOT / repo
    hg_dir = repo_dir / ".hg"

    if not repo_dir.is_dir() or not hg_dir.is_dir():
        print("%s is not an hg repository" % repo)
        sys.exit(1)

    try:
        return repo_dir.group()
    except Exception:
        sys.stderr.write("Warning: Couldn't stat %s" % repo_dir)
        print("Could not read %s" % repo)
        sys.exit(1)


# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
