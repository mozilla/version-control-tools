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
"""
This hook is to prevent changes to .webidl files in pushes without proper DOM peer review.
"""

import re
from mercurial.node import short
from mercurial import util

backoutMessage = [re.compile(x) for x in [
    r'^(back(ing|ed)?\s+out|backout)',
    r'^(revert(ed|ing)?)'
]]

def isBackout(message):
    for r in backoutMessage:
        if r.search(message):
            return True
    return False

def hook(ui, repo, hooktype, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    DOM_peers = [
        'jst',               # Johnny Stenback
        'peterv',            # Peter Van der Beken
        'bz', 'bzbarsky',    # Boris Zbarsky
        'sicking', 'jonas',  # Jonas Sicking
        'smaug',             # Olli Pettay
        'bent',              # Ben Turner
        'mounir',            # Mounir Lamouri
        'khuey',             # Kyle Huey
        'jlebar',            # Justin Lebar
        'hsivonen',          # Henri Sivonen
        'mrbkap',            # Blake Kaplan
        'bholley',           # Bobby Holley
        'baku',              # Andrea Marchesini
        'ehsan',             # Ehsan Akhgari
        'bkelly',            # Ben Kelly
        'billm',             # Bill McCloskey
        'qdot', 'kmachulis', # Kyle Machulis

        # Non-DOM peers who can review some WebIDL changes
        'hsinyi', 'htsai',   # Hsin-Yi Tsai for RIL APIs
    ]
    DOM_authors = [
        'jst@mozilla.com',         # Johnny Stenback
        'peterv@propagandism.org', # Peter Van der Beken
        'bzbarsky@mit.edu',        # Boris Zbarsky
        'jonas@sicking.cc',        # Jonas Sicking
        'olli.pettay@helsinki.fi', # Olli Pettay
        'bugs@pettay.fi',          # Olli Pettay
        'bent.mozilla@gmail.com',  # Ben Turner
        'mounir@lamouri.fr',       # Mounir Lamouri
        'khuey@kylehuey.com',      # Kyle Huey
        'justin.lebar@gmail.com',  # Justin Lebar
        'hsivonen@hsivonen.fi',    # Henri Sivonen
        'mrbkap@gmail.com',        # Blake Kaplan
        'amarchesini@mozilla.com', # Andrea Marchesini
        'ehsan@mozilla.com',       # Ehsan Akhgari
        'ehsan.akhgari@gmail.com', # Ehsan Akhgari
        'bkelly@mozilla.com',      # Ben Kelly
        'ben@wanderview.com',      # Ben Kelly
        'billm@mozilla.com',       # Bill McCloskey,
        'qdot@mozilla.com',        # Kyle Machulis
        'kmachulis@mozilla.com',   # Kyle Machulis
        'kyle@nonpolynomial.com',  # Kyle Machulis
    ]
    error = ""
    webidlReviewed = False
    changesets = list(repo.changelog.revs(repo[node].rev()))
    if 'a=release' in repo.changectx(changesets[-1]).description().lower():
        # Accept the entire push for code uplifts.
        return 0
    # Loop through each changeset being added to the repository
    for i in reversed(changesets):
        c = repo.changectx(i)

        if len(c.parents()) > 1:
            # Skip merge changesets
            continue

        # Loop through each file for the current changeset
        for file in c.files():
            # Only Check WebIDL Files
            if not file.endswith('.webidl'):
                continue

            # Ignore WebIDL files in Servo, which come from upstream and have
            # their own review process.
            if file.startswith('servo/'):
                ui.write('(%s modifies %s from Servo; not enforcing peer '
                         'review)\n' % (short(c.node()), file))
                continue

            message = c.description().lower()
            email = util.email(c.user()).lower()

            def search():
              matches = re.findall('\Ws?r\s*=\s*(\w+(?:,\w+)*)', message)
              for match in matches:
                  if any(reviewer in DOM_peers for reviewer in match.split(',')):
                      return True
              # We allow DOM peers to commit changes to WebIDL files without any review
              # requirements assuming that they have looked at the changes they're committing.
              if any(peer == email for peer in DOM_authors):
                  return True

              return False

            webidlReviewed = search()
            if not webidlReviewed and not isBackout(message):
                    error += "WebIDL file %s altered in changeset %s without DOM peer review\n" % (file, short(c.node()))
    # Check if an error occured in any of the files that were changed
    if error != "":
        print "\n\n************************** ERROR ****************************"
        ui.warn("\n" + error + "\n")
        print "\nChanges to WebIDL files in this repo require review from a DOM peer in the form of r=...\nThis is to ensure that we behave responsibly with exposing new Web APIs. We appreciate your understanding..\n"
        print "*************************************************************\n\n"
        # Reject the changesets
        return 1
    else:
        if webidlReviewed:
            print "You've received proper review from a DOM peer on your WebIDL change(s) in your push, thanks for paying enough attention."
    # Accept the changesets
    return 0
