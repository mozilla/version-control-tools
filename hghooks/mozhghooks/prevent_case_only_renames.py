#!/usr/bin/env python
# Copyright (C) 2011 Mozilla Foundation
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
"""
This hook is designed to prevent renames that only change the case of a file.
"""
from mercurial.node import hex, short

def hook(ui, repo, node, hooktype, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo.changectx(node).rev()
    tip = repo.changectx("tip").rev()
    rejecting = False

    for i in range(rev, tip + 1):
        ctx = repo.changectx(i)
        for f in ctx:
            fctx = ctx.filectx(f)
            r = fctx.renamed()
            if not r:
                continue
            if f.lower() == r[0].lower():
                rejecting = True
                print "\n\n************************** ERROR ****************************"
                print "File rename in changeset %s only changes file case! (%s to %s)" % (short(hex(ctx.node())), r[0], f)
                print "*************************************************************\n\n"
    return 1 if rejecting else 0
