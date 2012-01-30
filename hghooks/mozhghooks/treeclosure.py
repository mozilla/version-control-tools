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
    'birch'          : 'http://tinderbox.mozilla.org/Birch/status.html',
    'mozilla-aurora'  : 'http://tinderbox.mozilla.org/Mozilla-Aurora/status.html',
    'mozilla-beta'  : 'http://tinderbox.mozilla.org/Mozilla-Beta/status.html',
    'mozilla-release'  : 'http://tinderbox.mozilla.org/Mozilla-Release/status.html',
    'mozilla-esr10'  : 'http://tinderbox.mozilla.org/Mozilla-Esr10/status.html',
    'mozilla-central': 'http://tinderbox.mozilla.org/Firefox/status.html',
    'mozilla-inbound': 'http://tinderbox.mozilla.org/Mozilla-Inbound/status.html',
    'mozilla-2.1'    : 'http://tinderbox.mozilla.org/Mobile2.0/status.html',
    'mozilla-2.0'    : 'http://tinderbox.mozilla.org/Firefox4.0/status.html',
    'mozilla-1.9.1'  : 'http://tinderbox.mozilla.org/Firefox3.5/status.html',
    'mozilla-1.9.2'  : 'http://tinderbox.mozilla.org/Firefox3.6/status.html',
    'mobile-browser' : 'http://tinderbox.mozilla.org/Mobile/status.html',
    'mobile-2.0'     : 'http://tinderbox.mozilla.org/Mobile2.0/status.html',
    'mobile-1.1'     : 'http://tinderbox.mozilla.org/Mobile1.1/status.html',
    'mobile-5.0'     : 'http://tinderbox.mozilla.org/Mobile5.0/status.html',
    'mobile-6.0'     : 'http://tinderbox.mozilla.org/Mobile6.0/status.html',
    'mozilla-mobile-6.0'     : 'http://tinderbox.mozilla.org/Mobile6.0/status.html',
    'mozilla-mobile-5.0' : 'http://tinderbox.mozilla.org/Mobile5.0/status.html',
    'places'         : 'http://tinderbox.mozilla.org/Places/status.html',
    'electrolysis'   : 'http://tinderbox.mozilla.org/Electrolysis/status.html',
    'tracemonkey'    : 'http://tinderbox.mozilla.org/TraceMonkey/status.html',
    'try'            : 'http://tinderbox.mozilla.org/Try/status.html',
    'try-comm-central': 'http://tinderbox.mozilla.org/ThunderbirdTry/status.html',
    'services-central': 'http://tinderbox.mozilla.org/Services-Central/status.html',
    'shadow-central' : 'http://tinderbox.mozilla.org/Shadow-Central/status.html',
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
        if re.compile('<span id="tree-?status".*CLOSED.*<span id="extended-status">').search(text) :
            print "Tree %s is CLOSED! (%s)" % (name, url)
            
            # Block the push unless they know the magic words
            if repo.changectx('tip').description().find(magicwords) == -1:
                print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
                return 1

            print "But you included the magic words.  Hope you had permission!"
            return 0
        elif re.compile('<span id="tree-?status".*APPROVAL REQUIRED.*<span id="extended-status">').search(text) :
            # Block the push unless they have approval
            if re.search('a\S*=', repo.changectx('tip').description().lower()) :
                return 0

            print "Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)"
            return 1
        elif not re.compile('<span id="tree-?status".*<span id="extended-status">').search(text):
            print "The extended status span must be on the same line as the treestatus."
            return 1
            
    except IOError, (err):
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
