#!/usr/bin/env python

# Copyright (C) 2013 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os.path

from treeclosure import isPushAllowed

# Array of which directories SeaMonkey exclusively controls in comm-central
seamonkeyOwns = [
  'suite'
]
# Array of which directories Instantbird exclusively controls in comm-central
instantbirdOwns = [
  'im'
]
# Everything else is assumed to be controlled by Thunderbird.


def isOwned(changedFile, ownerArray):
    for dir in ownerArray:
        if os.path.commonprefix([changedFile, dir]) == dir:
            return True

    return False


def hook(ui, repo, node, source=None, **kwargs):
    if source == 'strip':
        return 0

    try:
        # First find out which trees are affected
        apps = { 'thunderbird' : False,
                 'seamonkey' : False }

        # all changesets from node to 'tip' inclusive are part of this push
        rev = repo.changectx(node).rev()
        tip = repo.changectx('tip').rev()
        for i in range(rev, tip+1):
            ctx = repo.changectx(i)
            for changedFile in ctx.files():
                if isOwned(changedFile, seamonkeyOwns):
                    apps['seamonkey'] = True
                elif isOwned(changedFile, instantbirdOwns):
                    pass  # ignore Instantbird for tree closure reasons
                else:
                    apps['thunderbird'] = True

        repoName = os.path.basename(repo.root)

        for app in apps:
            if apps[app]:
                treestatus_name = "%s-%s" % (repoName, app)
                if not isPushAllowed(repo, treestatus_name):
                    return 1

    except IOError, (err):
        #TODO: Below obsolete?
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
