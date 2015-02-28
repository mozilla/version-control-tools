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

from urllib2 import urlopen
import os.path
import re
import json

magicwords = "CLOSED TREE"

treestatus_base_url = "https://treestatus.mozilla.org"

def printError(message):
    print "\n\n************************** ERROR ****************************"
    print message
    print "*************************************************************\n\n"

def hook(ui, repo, source=None, **kwargs):
    if source == 'strip':
        return 0

    name = os.path.basename(repo.root)
    url = "%s/%s?format=json" % (treestatus_base_url, name)
    try:
        u = urlopen(url)
        data = json.load(u)
        if data['status'] == 'closed':
            closure_text = "%s is CLOSED! Reason: %s" % (name, data['reason'])
            # Block the push unless they know the magic words
            if repo.changectx('tip').description().find(magicwords) == -1:
                printError("%s\nTo push despite the closed tree, include \"%s\" in your push comment" % (closure_text, magicwords))
                return 1

            print "%s\nBut you included the magic words.  Hope you had permission!" % closure_text
            return 0
        elif data['status'] == 'approval required':
            # Block the push unless they have approval or are backing out
            dlower = repo.changectx('tip').description().lower()
            if re.search('a\S*=', dlower) or dlower.startswith('back') or dlower.startswith('revert'):
                return 0

            printError("Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)")
            return 1

    except (ValueError, IOError), (err):
        # fail closed if treestatus is down, unless the magic words have been used
        printError("Error accessing %s :\n"
                   "%s\n"
                   "Unable to check if the tree is open - treating as if CLOSED.\n"
                   "To push regardless, include \"%s\" in your push comment." % (url, err, magicwords))
        if repo.changectx('tip').description().find(magicwords) == -1:
            return 1
    return 0
