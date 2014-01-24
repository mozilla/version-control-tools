#!/usr/bin/python
# Copyright (C) 2012 Mozilla Foundation
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
This hook prevents changes from being made to Australis-related files,
unless the commit message contains "australis" or an override string.
"""
from mercurial.node import short


def printError(c):
    print "\n\n************************** ERROR ****************************"
    print "Changeset %s appears to make australis changes, but does" % short(c.node())
    print "not contain \"australis\" in the commit message! (See bug 943486)"
    print " -> \"%s\"" % c.description()
    print "*************************************************************"


def hook(ui, repo, node, hooktype, **kwargs):
    changesets = list(repo.changelog.revs(repo[node].rev()))
    rejecting = False

    # All changesets in this push, starting at tip (so the override works).
    # Note: Unless the override was used, we do not break the outer loop, so
    # that the pusher can see all of the commits that need fixing in one go.
    for i in reversed(changesets):
        c = repo.changectx(i)

        desc = c.description()

        if "OVERRIDE HOOK" in desc:
            # Skip all earlier commits in this push.
            break

        if "australis" in desc.lower():
            # This commit is labelled correctly, proceed to the next.
            continue

        if len(c.parents()) > 1:
            # Skip merge changesets
            continue

        for file in c.files():
            if ((file.startswith("browser/themes/") and "devtools" not in file) or
                    file.startswith("browser/components/customizableui/")):
                # Australis-related files found.
                rejecting = True
                printError(c)
                break

    return 1 if rejecting else 0
