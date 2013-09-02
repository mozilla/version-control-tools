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
This hook is to prevent changes to IID or UUID in pushes to trees where such changes could cause critical issues (eg: beta, release).
"""

import os,re
from mercurial import ui

def hook(ui, repo, hooktype, node, **kwargs):
    error = ""
    bc = False
    # Loop through each changeset being added to the repository
    for change_id in xrange(repo[node].rev(), len(repo)):
        # Loop through each file for the current changeset
        for file in repo[change_id].files():
            # Only Check IDL Files
            if file.endswith('.idl'):
                if not re.search('ba\S*=', repo.changectx('tip').description().lower()):
                        error += "IDL file %s altered in this changeset" % file
    # Check if an error occured in any of the files that were changed
    if error != "":
        print "\n\n************************** ERROR ****************************"
        ui.warn("\n\r*** " + error + "***\n\r")
        print "\n\rChanges to IDL files in this repo require you to provide binary change approval in your top comment in the form of ba=... (or, more accurately, ba\\S*=...)\n\rThis is to ensure that UUID changes (or method changes missing corresponding UUID change) are caught early, before release.\n\r"
        print "*************************************************************\n\n"
        # Reject the changesets
        return 1
    else:
        if bc:
            print "You've signaled approval for the binary change(s) in your push, thanks for the extra caution."
    # Accept the changesets
    return 0
