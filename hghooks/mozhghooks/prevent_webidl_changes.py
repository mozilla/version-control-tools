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
This hook is to prevent changes to .webidl files in pushes without proper DOM peer review.
"""

import re
from mercurial.node import short

def hook(ui, repo, hooktype, node, **kwargs):
    DOM_peers = [
        'jst',              # Johnny Stenback
        'peterv',           # Peter Van der Beken
        'bz', 'bzbarsky',   # Boris Zbarsky
        'sicking', 'jonas', # Jonas Sicking
        'smaug',            # Olli Pettay
        'bent',             # Ben Turner
        'mounir',           # Mounir Lamouri
        'khuey',            # Kyle Huey
        'jlebar',           # Justin Lebar
        'hsivonen',         # Henri Sivonen
        'mrbkap',           # Blake Kaplan
        'bholley',          # Bobby Holley
    ]
    error = ""
    webidlReviewed = False
    # Loop through each changeset being added to the repository
    changesets = list(repo.changelog.revs(repo[node].rev()))
    for i in reversed(changesets):
        c = repo.changectx(i)

        if len(c.parents()) > 1:
            # Skip merge changesets
            continue

        # Loop through each file for the current changeset
        for file in c.files():
            # Only Check WebIDL Files
            if file.endswith('.webidl'):
                webidlReviewed = True
                match = re.search('\Wr\s*=\s*(\w+(?:,\w+)*)', c.description().lower())
                validReview = False
                if match:
                    for reviewer in match.group(1).split(','):
                        if reviewer in DOM_peers:
                            validReview = True
                            break
                if not validReview:
                        error += "WebIDL file %s altered in changeset %s without DOM peer review\n" % (file, short(c.node()))
    # Check if an error occured in any of the files that were changed
    if error != "":
        print "\n\n************************** ERROR ****************************"
        ui.warn("\n" + error + "\n")
        print "\n\rChanges to WebIDL files in this repo require review from a DOM peer in the form of r=...\n\rThis is to ensure that we behave responsibly with exposing new Web APIs. We appreciate your understanding..\n\r"
        print "*************************************************************\n\n"
        # Reject the changesets
        return 1
    else:
        if webidlReviewed:
            print "You've received proper review from a DOM peer on your WebIDL change(s) in your push, thanks for paying enough attention."
    # Accept the changesets
    return 0
