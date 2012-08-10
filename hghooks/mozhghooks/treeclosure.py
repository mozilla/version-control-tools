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

def hook(ui, repo, **kwargs):
    name = os.path.basename(repo.root)
    url = "%s/%s?format=json" % (treestatus_base_url, name)
    try:
        u = urlopen(url)
        data = json.load(u)
        if data['status'] == 'closed':
            print "Tree %s is CLOSED! (%s) - %s" % (name, url, data['reason'])

            # Block the push unless they know the magic words
            if repo.changectx('tip').description().find(magicwords) == -1:
                print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
                return 1

            print "But you included the magic words.  Hope you had permission!"
            return 0
        elif data['status'] == 'approval required':
            # Block the push unless they have approval
            if re.search('a\S*=', repo.changectx('tip').description().lower()) :
                return 0

            print "Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)"
            return 1

    except (ValueError, IOError), (err):
        # fail open. no sense making hg unavailable
        # if treestatus is down
        print "Error: %s" % err, url
        pass
    return 0
