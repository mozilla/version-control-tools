#!/usr/bin/env python

#import cgi
#import cgitb
from grp import getgrgid
import hg_helper
import os
import sys

def repo_owner(repo):
    repo_root = "/repo/hg/mozilla"

    if not repo:
        print "Need a repository to check"
        sys.exit(1)

    if not hg_helper.check_repo_name(repo):
        print "You've included some illegal characters in your repo name"
        sys.stderr.write("Warning: illegal characters in repo name\n")
        sys.exit(1)

    # ensure that the repo is within repo_root
    if repo.find('/../') != -1:
        print "That's not allowed"
        sys.stderr.write("Warning: /../ found in a repo name.\n")
        sys.exit(1)

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
