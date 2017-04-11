#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from grp import getgrgid
import hg_helper
import os
import sys

def repo_owner(repo):
    repo_root = "/repo/hg/mozilla"

    if not repo:
        print "Need a repository to check"
        sys.exit(1)

    hg_helper.assert_valid_repo_name(repo)

    dir = "%s/%s" % (repo_root, repo)

    if not (os.path.isdir(dir) and os.path.isdir(dir + "/.hg")):
        print "%s is not an hg repository" % repo
        sys.exit(1)

    try:
        fdata = os.stat(dir)
    except:
        sys.stderr.write("Warning: Couldn't stat %s" % dir)
        print "Could not read %s" % repo
        sys.exit(1)

    gid = fdata.st_gid
    group = getgrgid(gid)[0]
    return group

# Local variables:
# mode: python
# indent-tabs-mode: nil
# tab-width: 4
# end:
