#!/usr/bin/env python

def hook(ui, repo, **kwargs):
    for b in repo.branchtags():
        if len(repo.branchheads(b)) > 1:
            print "Two heads detected on branch '%s'" % b
            print "Only one head per branch is allowed!"
            return 1
    return 0
