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

# This script implements a whitelist containing people from the releng and
# relops teams.
#
# run `python setup.py install` to install the module in the proper place,
# and then modify the repository's hgrc as per example-hgrc.

import os

ALLOWED_USERS = set([
    b'Callek@gmail.com',
    b'asasaki@mozilla.com',
    b'arich@mozilla.com',
    b'bhearsum@mozilla.com',
    b'catlee@mozilla.com',
    b'dcrisan@mozilla.com',
    b'dhouse@mozilla.com',
    b'jlorenzo@mozilla.com',
    b'jlund@mozilla.com',
    b'jwatkins@mozilla.com',
    b'jwood@mozilla.com',
    b'klibby@mozilla.com',
    b'kmoir@mozilla.com',
    b'mcornmesser@mozilla.com',
    b'nthomas@mozilla.com',
    b'qfortier@mozilla.com',
    b'raliiev@mozilla.com',
    b'aselagea@mozilla.com',
    b'mtabara@mozilla.com',
    b'sfraser@mozilla.com',
    b'aobreja@mozilla.com',
    b'mozilla@hocat.ca',  # Tom Prince
])


def hook(ui, repo, node=None, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    rev = repo[node].rev()
    tip = repo[b'tip'].rev()
    branches = set(repo[i].branch() for i in range(rev, tip + 1))
    if b'production' in branches and os.environ[b'USER'] not in ALLOWED_USERS:
        print b"** you (%s) are not allowed to push to the production branch" \
            % (os.environ[b'USER'],)
        return 1
    return 0
