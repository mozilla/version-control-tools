#!/usr/bin/env python

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

from mercurial import (
    urllibcompat,
)
import os.path
import re
import json

from mercurial import (
    pycompat,
)

magicwords = b"CLOSED TREE"


def printError(ui, message):
    ui.write(b"\n\n************************** ERROR ****************************\n")
    ui.write(message)
    ui.write(b"*************************************************************\n\n\n")


def isPushAllowed(ui, repo, name):
    treestatus_base_url = ui.config(
        b"mozilla",
        b"treestatus_base_url",
        b"https://treestatus.prod.lando.prod.cloudops.mozgcp.net/trees/%s",
    )
    url = treestatus_base_url % (name,)
    try:
        request = urllibcompat.urlreq.request(pycompat.sysstr(url))
        u = urllibcompat.urlreq.urlopen(request)
        data = json.load(u)
        if data["result"]["status"] == "closed":
            closure_text = b"%s is CLOSED! Reason: %s" % (
                name,
                pycompat.bytestr(data["result"]["reason"]),
            )
            # Block the push unless they know the magic words
            if repo[b"tip"].description().find(magicwords) == -1:
                printError(
                    ui,
                    b'%s\nTo push despite the closed tree, include "%s" in your push comment\n'
                    % (closure_text, magicwords),
                )
                return False

            ui.write(
                b"%s\nBut you included the magic words.  Hope you had permission!\n"
                % closure_text
            )
        elif data["result"]["status"] == "approval required":
            # Block the push unless they have approval or are backing out
            dlower = repo[b"tip"].description().lower()
            if not (
                re.search(rb"a\S*=", dlower)
                or dlower.startswith(b"back")
                or dlower.startswith(b"revert")
            ):
                printError(
                    ui,
                    b"Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: "
                    b"a=... (or, more accurately, a\\S*=...)\n",
                )
                return False

    except (ValueError, IOError) as err:
        # fail closed if treestatus is down, unless the magic words have been used
        printError(
            ui,
            b"Error accessing %s :\n"
            b"%s\n"
            b"Unable to check if the tree is open - treating as if CLOSED.\n"
            b'To push regardless, include "%s" in your push comment.\n'
            % (url, pycompat.bytestr(str(err)), magicwords),
        )
        if repo[b"tip"].description().find(magicwords) == -1:
            return False
    return True


def hook(ui, repo, source=None, **kwargs):
    if source in (b"pull", b"strip"):
        return 0

    treestatus_name = os.path.basename(repo.root)
    return 0 if isPushAllowed(ui, repo, treestatus_name) else 1
