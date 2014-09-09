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

def log(ui, repo, node, **kwargs):
    if not hasattr(repo, 'pushlog'):
        ui.write('repository not properly configured; missing pushlog extension.\n')
        return 1

    # As long as the pushlog extension is installed, we should never get
    # here because the extension installs its own hook which overwrites
    # us.
    ui.write('Assertion failure: the pushlog hook code should not run any more. '
        'Please file a bug.\n')
    return 1
