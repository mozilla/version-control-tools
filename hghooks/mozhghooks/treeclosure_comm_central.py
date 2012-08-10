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

# Array of which directories Calendar exclusively controls in comm-central
calendarOwns = [
  'calendar',
  'other-licenses/branding/sunbird'
]

# Array of which directories SeaMonkey exclusively controls in comm-central
seamonkeyOwns = [
  'suite'
]
# Everything else is assumed to be controlled by Thunderbird.

# SeaMonkey tinderbox trees
seamonkeyTrees = {
  'comm-central': 'http://tinderbox.mozilla.org/SeaMonkey/status.html',
  'comm-aurora' : 'http://tinderbox.mozilla.org/SeaMonkey-Aurora/status.html',
  'comm-beta'   : 'http://tinderbox.mozilla.org/SeaMonkey-Beta/status.html',
  'comm-release': 'http://tinderbox.mozilla.org/SeaMonkey-Release/status.html',
  'comm-esr10'  : None,
  # Point at Mirmar as SeaMonkey doesn't use this
  'comm-miramar': None,
  'comm-2.0'    : 'http://tinderbox.mozilla.org/SeaMonkey2.1/status.html',
  'comm-1.9.1'  : 'http://tinderbox.mozilla.org/SeaMonkey2.0/status.html',
  # Point at Thunderbird as SeaMonkey doesn't use this.
  'comm-1.9.2'  : None,
}
# Calendar tinderbox trees
calendarTrees = {
  'comm-central': 'http://tinderbox.mozilla.org/CalendarTrunk/status.html',
  # Point at Thunderbird for now
  'comm-aurora' : 'http://tinderbox.mozilla.org/Calendar-Aurora/status.html',
  # Point at Thunderbird for now
  'comm-beta'   : 'http://tinderbox.mozilla.org/Calendar-Beta/status.html',
  'comm-release': 'http://tinderbox.mozilla.org/Calendar-Release/status.html',
  'comm-esr10'  : None,
  'comm-miramar': None,
  # Point at SeaMonkey as Calendar don't use this one
  'comm-2.0'    : None,
  # Point at Thunderbird as Calendar doesn't use this
  'comm-1.9.2'  : None,
  # Point at SeaMonkey as Calendar doesn't use this.
  'comm-1.9.1'  : None,
}


magicwords = "CLOSED TREE"

treestatus_base_url = "https://treestatus.mozilla.org"

# This function actually does the checking to see if a tree is closed or set
# to approval required.
def checkTreeState(repo, repoName, treeName, treeUrl):
    if not treeUrl:
        # Fail open for trees that we don't have a url for.
        return 0

    # Get the tree state from tinderbox
    try:
        u = urlopen(treeUrl)
    except IOError, e:
        # If tinderbox is down, allow pushes
        print "Tinderbox may be down, allowing your push, but you'd better check!"
        return 0

    text = ''.join(u.readlines()).strip()

    if re.compile('<span id="tree-?status".*CLOSED.*<span id="extended-status">').search(text) :
        # The tree is closed

        # Tell the pusher
        print "Tree %s is CLOSED! (%s, %s)" % (treeName, repoName, treeUrl)
        print repo.changectx('tip').description()

        # Block the push if no magic words
        if repo.changectx('tip').description().find(magicwords) == -1:
            print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
            return 1

        # Otherwise let them push
        print "But you included the magic words.  Hope you had permission!"
        return 0

    elif re.compile('<span id="tree-?status".*APPROVAL REQUIRED.*<span id="extended-status">').search(text) :
        # The tree needs approval

        # If they've specified an approval, let them push 
        if re.search('a\S*=', repo.changectx('tip').description().lower()) :
            return 0

        # Otherwise tell them about the rule
        print "Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)"

        # And block the push
        return 1

    elif not re.compile('<span id="tree-?status".*<span id="extended-status">').search(text):
        print "The extended status span must be on the same line as the treestatus."
        return 1

    # By default the tree is open
    return 0

def checkJsonTreeState(repo, repoName, appName):
    name = os.path.basename(repo.root)
    url = "%s/%s-%s?format=json" % (treestatus_base_url, name, appName)
    try:
        u = urlopen(url)
        data = json.load(u)

        if data['status'] == 'closed':
            # The tree is closed

            # Tell the pusher
            print "Tree %s %s is CLOSED!" % (appName.capitalize(), name)
            print repo.changectx('tip').description()

            # Block the push if no magic words
            if repo.changectx('tip').description().find(magicwords) == -1:
                print "To push despite the closed tree, include \"%s\" in your push comment" % magicwords
                return 1

            # Otherwise let them push
            print "But you included the magic words.  Hope you had permission!"
            return 0

        elif data['status'] == 'approval required':
            # The tree needs approval

            # If they've specified an approval, let them push 
            if re.search('a\S*=', repo.changectx('tip').description().lower()) :
                return 0

            # Otherwise tell them about the rule
            print "Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\\S*=...)"
            return 1

    except IOError, (err):
        # fail open, I guess. no sense making hg unavailable
        # if treestatus is down
        print "Error: %s" % err, url
        pass

    # By default the tree is open
    return 0
        

def isOwned(changedFile, ownerArray):
    for dir in ownerArray:
        if os.path.commonprefix([changedFile, dir]) == dir:
            return True

    return False

def hook(ui, repo, node, **kwargs):
    try:
        # First find out which trees are affected
        apps = { 'thunderbird' : False,
                 'seamonkey' : False,
                 'calendar' : False }

        # all changesets from node to 'tip' inclusive are part of this push
        rev = repo.changectx(node).rev()
        tip = repo.changectx('tip').rev()
        for i in range(rev, tip+1):
            ctx = repo.changectx(i)
            for changedFile in ctx.files():
                if isOwned(changedFile, seamonkeyOwns):
                    apps['seamonkey'] = True
                elif isOwned(changedFile, calendarOwns):
                    apps['calendar'] = True
                else:
                    apps['thunderbird'] = True

        affectedTrees = []
        repoName = os.path.basename(repo.root)
        status = 0

        # This can be replaced by "for app in apps:" once all apps have switched.
        for app in ['thunderbird']:
            if apps[app]:
                status = checkJsonTreeState(repo, repoName, app)
                if status == 1:
                    return 1

        if apps['seamonkey']:
            if not seamonkeyTrees.has_key(repoName):
                print "Unrecognized tree!  I don't know how to check closed status for %s and SeaMonkey... allowing push, but you should report this!" % (repoName)
            else:
                status = checkTreeState(repo, repoName, 'SeaMonkey', seamonkeyTrees[repoName])
                if status == 1:
                    return 1

        if apps['calendar']:
            if not calendarTrees.has_key(repoName):
                print "Unrecognized tree!  I don't know how to check closed status for %s and Calendar... allowing push, but you should report this!" % (repoName)
            else:
                 status = checkTreeState(repo, repoName, 'Calendar', calendarTrees[repoName])

        return status;
        
            
    except IOError, (err):
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
