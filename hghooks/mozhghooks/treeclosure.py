#!/usr/bin/env python
from urllib import urlopen
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
    'tracemonkey'    : 'http://tinderbox.mozilla.org/TraceMonkey/'
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
            if repo.changectx('tip').description().find(magicwords) < 0:
                print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
                return 1
            else:
                print "But you included the magic words.  Hope you had permission!"
                return 0
    except IOError, (err):
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
