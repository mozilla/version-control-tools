#!/usr/bin/env python

# Copyright (C) 2013 Mozilla Foundation
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

# Array of which directories SeaMonkey exclusively controls in comm-central
seamonkeyOwns = [
  'suite'
]
# Everything else is assumed to be controlled by Thunderbird.

magicwords = "CLOSED TREE"

treestatus_base_url = "https://treestatus.mozilla.org"

def printError(message):
    print "\n\n************************** ERROR ****************************"
    print message
    print "*************************************************************\n\n"

# This function actually does the checking to see if a tree is closed or set
# to approval required.
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
                printError("To push despite the closed tree, include \"%s\" in your push comment" % magicwords)
                return 1

            # Otherwise let them push
            print "But you included the magic words.  Hope you had permission!"
            return 0

        elif data['status'] == 'approval required':
            # The tree needs approval

            # If they've specified an approval or are backing out, let them push
            dlower = repo.changectx('tip').description().lower()
            if re.search('a\S*=', dlower) or dlower.startswith('back') or dlower.startswith('revert'):
                return 0

            # Otherwise tell them about the rule
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
                 'seamonkey' : False }

        # all changesets from node to 'tip' inclusive are part of this push
        rev = repo.changectx(node).rev()
        tip = repo.changectx('tip').rev()
        for i in range(rev, tip+1):
            ctx = repo.changectx(i)
            for changedFile in ctx.files():
                if isOwned(changedFile, seamonkeyOwns):
                    apps['seamonkey'] = True
                else:
                    apps['thunderbird'] = True

        repoName = os.path.basename(repo.root)
        status = 0

        for app in apps:
            if apps[app]:
                status = checkJsonTreeState(repo, repoName, app)
                if status == 1:
                    return 1

        return status;

    except IOError, (err):
        #TODO: Below obsolete?
        # fail open, I guess. no sense making hg unavailable
        # if the wiki is down
        print "IOError: %s" % err
        pass
    return 0
