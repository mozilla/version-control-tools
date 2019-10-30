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

from __future__ import absolute_import

import os.path

from mozhghooks.treeclosure import isPushAllowed

# Array of which directories SeaMonkey exclusively controls in comm-central
seamonkeyOwns = [
  b'suite'
]
# Array of which directories Instantbird exclusively controls in comm-central
instantbirdOwns = [
  b'im'
]
# Everything else is assumed to be controlled by Thunderbird.


def isOwned(changedFile, ownerArray):
    for dir in ownerArray:
        if os.path.commonprefix([changedFile, dir]) == dir:
            return True

    return False


def hook(ui, repo, node, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    # First find out which trees are affected
    apps = {b'thunderbird': False,
            b'seamonkey': False}

    # all changesets from node to 'tip' inclusive are part of this push
    rev = repo[node].rev()
    tip = repo[b'tip'].rev()
    for i in range(rev, tip+1):
        ctx = repo[i]
        for changedFile in ctx.files():
            if isOwned(changedFile, seamonkeyOwns):
                apps[b'seamonkey'] = True
            elif isOwned(changedFile, instantbirdOwns):
                pass  # ignore Instantbird for tree closure reasons
            else:
                apps[b'thunderbird'] = True

    repoName = os.path.basename(repo.root)

    for app in apps:
        if apps[app]:
            treestatus_name = b"%s-%s" % (repoName, app)
            if not isPushAllowed(ui, repo, treestatus_name):
                return 1

    return 0
