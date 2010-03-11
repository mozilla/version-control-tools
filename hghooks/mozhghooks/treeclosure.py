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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from urllib2 import urlopen
import os.path
import re

hgNameToTinderboxURL = {
    'mozilla-central': 'http://tinderbox.mozilla.org/Firefox/',
    'comm-central'   : 'http://tinderbox.mozilla.org/Thunderbird/',
    'mozilla-1.9.1'  : 'http://tinderbox.mozilla.org/Firefox3.5/',
    'mozilla-1.9.2'  : 'http://tinderbox.mozilla.org/Firefox3.6/',
    'mobile-browser' : 'http://tinderbox.mozilla.org/Mobile/',
    'places'         : 'http://tinderbox.mozilla.org/Places/',
    'electrolysis'   : 'http://tinderbox.mozilla.org/Electrolysis/',
    'tracemonkey'    : 'http://tinderbox.mozilla.org/TraceMonkey/',
    'try'            : 'http://tinderbox.mozilla.org/MozillaTry/'
}

magicwords = "CLOSED TREE"

def hook(ui, repo, **kwargs):
    try:
        name = os.path.basename(repo.root)
        if not hgNameToTinderboxURL.has_key(name) :
            print "Unrecognized tree!  I don't know how to check closed status for %s." % name
            return 1;
        
        url = hgNameToTinderboxURL[name];
        u = urlopen(url)
        text = ''.join(u.readlines()).strip()
        if re.compile('<span id="treestatus".*CLOSED.*<span id="extended-status">').search(text) :
            print "Tree %s is CLOSED! (%s)" % (name, url)
            
            # Block the push unless they know the magic words
            if repo.changectx('tip').description().find(magicwords) == -1:
                print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
                return 1

            print "But you included the magic words.  Hope you had permission!"
            return 0
        elif re.compile('<span id="treestatus".*APPROVAL REQUIRED.*<span id="extended-status">').search(text) :
            # Block the push unless they have approval
            if re.search('a\S*=', repo.changectx('tip').description().lower()) :
                return 0

            print "Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)"
            return 1
            
    except IOError, (err):
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
