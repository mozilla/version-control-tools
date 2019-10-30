#!/usr/bin/env python
# Copyright (C) 2014 Mozilla Foundation
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
This hook is to prevent changes to strings in string frozen branches without
explicit approval from l10n-drivers. Can be bypassed adding l10n= followed by
an approver to the commit message (case sensitive), see bug 859358 for further
details.
"""

import re


def hook(ui, repo, hooktype, node, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    error = b""
    changed_strings = False
    if b'a=release' in repo[b'tip'].description().lower():
        # Accept the entire push for code uplifts
        return 0
    # Loop through each changeset being added to the repository
    for change_id in xrange(repo[node].rev(), len(repo)):
        # Loop through each file for the current changeset
        for file in repo[change_id].files():
            # Interested only in files potentially used for l10n
            if (re.search(b'locales/en-US/', file) and file.endswith((b'.dtd', b'.ini', b'.properties'))):
                changed_strings = True
                if not re.search(b'l10n=', repo[b'tip'].description().lower()):
                    error += b"* File used for localization (%s) altered in this changeset *\n" % file
    # Check if an error occurred
    if error != b"":
        ui.write(b"\n************************** ERROR ****************************\n\n")
        ui.write(error)
        ui.write(b"\nThis repository is string frozen. Please request explicit permission from\n")
        ui.write(b"release managers to break string freeze in your bug.\n")
        ui.write(b"If you have that explicit permission, denote that by including in\n")
        ui.write(b"your commit message l10n=...\n")
        ui.write(b"*************************************************************\n\n")
        # Reject the changesets
        return 1
    else:
        if changed_strings:
            ui.write(b"You've signaled approval for changes to strings in your push, thanks.\n")
    # Accept the changesets
    return 0
