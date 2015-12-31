#!/usr/bin/env python
# Copyright (C) 2015 Mozilla Foundation
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
This hook checks that people using a=css-image-only are in fact only touching
such files (ie CSS/images/jar.mn).
"""


def hook(ui, repo, hooktype, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    if 'a=css-image-only' not in repo['tip'].description().lower():
        # We only care if the 'css-image-only' approval message was used
        return 0

    errors = []
    # Loop through each changeset being added to the repository
    for change_id in xrange(repo[node].rev(), len(repo)):
        # Loop through each file for the current changeset
        for changed_file in repo[change_id].files():
            # Check they have an expected extension:
            if not changed_file.endswith(('.css', 'jar.mn', '.png', '.jpg', '.svg')):
                errors.append('* non-image/css-file (%s) altered in this changeset\n' % changed_file)

    if errors:
        print('\n************************** ERROR ****************************')
        print('\n'.join(errors))
        print('You used the a=css-image-only approval message, but your change')
        print('included non-CSS/image/jar.mn changes. Please get "normal"')
        print('approval from release management for your changes.')
        print('*************************************************************\n')
        # Reject changes
        return 1
    print('Thanks for your a=css-image-only push, it\'s the best!')

    # Otherwise, accept changes
    return 0
