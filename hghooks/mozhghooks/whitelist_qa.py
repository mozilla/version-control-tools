#!/usr/bin/env python

# Copyright (C) 2010 Mozilla Foundation
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

# This script implements a whitelist containing people from the QA team (plus
# Dustin)
#
# run `python setup.py install` to install the module in the proper place,
# and then modify the repository's hgrc as per example-hgrc.

import os

ALLOWED_USERS = set([
    'dmitchell@mozilla.com',
    'hskupin@mozilla.com',
])


def hook(ui, repo, node=None, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    rev = repo[node].rev()
    tip = repo['tip'].rev()
    branches = set(repo.changectx(i).branch() for i in range(rev, tip + 1))
    if 'production' in branches and os.environ['USER'] not in ALLOWED_USERS:
        print "** you (%s) are not allowed to push to the production branch" \
            % (os.environ['USER'],)
        return 1
    return 0
