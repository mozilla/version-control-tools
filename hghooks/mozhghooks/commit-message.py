#!/usr/bin/env python
# Copyright (C) 2011 Mozilla Foundation
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

import re
from mercurial.node import hex, short

INVALID_REVIEW_FLAG_RE = re.compile(r'[\s.;]r\?(?:\w|$)')

goodMessage = [re.compile(x, re.I) for x in [
    r'bug [0-9]+',
    r'no bug',

    r'^(back(ing|ed)?\s+out|backout).*(\s+|\:)[0-9a-f]{12}',
    r'^(revert(ed|ing)?).*(\s+|\:)[0-9a-f]{12}',
    r'^add(ed|ing)? tag'
]]

trySyntax = re.compile(r'\btry:')

VENDORED_PATHS = (
    'servo/',
)


def is_vendor_ctx(ctx):
    # This check isn't strictly necessary. But it does filter out
    # most changesets without having to inspect the file list.
    desc = ctx.description()
    if 'Source-Revision: ' not in desc:
        return False

    # Other hooks should ensure that only certain users can change
    # vendored paths.
    if not any(f.startswith(VENDORED_PATHS) for f in ctx.files()):
        return False

    return True


def is_good_message(ui, c):
    def message(fmt):
        ui.write(
            '\n\n'
            '************************** ERROR ****************************\n'
            '%s\n%s\n%s\n'
            '*************************************************************\n'
            '\n\n'
            % (fmt.format(rev=hex(c.node())[:12]), c.user(), c.description())
        )

    if is_vendor_ctx(c):
        ui.write('(%s looks like a vendoring change; ignoring commit message '
                 'hook)\n' % short(c.node()))
        return True

    desc = c.description()
    firstline = desc.splitlines()[0]

    if c.user() in ["ffxbld", "seabld", "tbirdbld", "cltbld"]:
        return True

    if trySyntax.search(desc):
        message("Rev {rev} uses try syntax. (Did you mean to push to Try "
                "instead?)")
        return False

    # Match against [PATCH] and [PATCH n/m]
    if "[PATCH" in desc:
        message('Rev {rev} contains git-format-patch "[PATCH]" cruft. Use '
                'git-format-patch -k to avoid this.')
        return False

    if INVALID_REVIEW_FLAG_RE.search(firstline):
        message("Rev {rev} contains 'r?' in the commit message. Please use "
                "'r=' instead.")
        return False

    for r in goodMessage:
        if r.search(firstline):
            return True

    desc_lower = desc.lower()
    if desc_lower.startswith(('merge', 'merging', 'automated merge')):
        if len(c.parents()) == 2:
            return True
        else:
            message("Rev {rev} claims to be a merge, but it has only one "
                    "parent.")
            return False

    if desc_lower.startswith(('back', 'revert')):
        # Purposely ambiguous: it's ok to say "backed out rev N" or
        # "reverted to rev N-1"
        message("Backout rev {rev} needs a bug number or a rev id.")
    else:
        message('Rev {rev} needs "Bug N" or "No bug" in the commit message.')

    return False


def hook(ui, repo, node, hooktype, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo.changectx(node).rev()
    tip = repo.changectx("tip").rev()
    rejecting = False

    for i in reversed(xrange(rev, tip + 1)):
        c = repo.changectx(i)

        if "IGNORE BAD COMMIT MESSAGES" in c.description():
            # Ignore commit messages for all earlier revs in this push.
            break

        if not is_good_message(ui, c):
            # Keep looping so the pusher sees all commits they need to fix.
            rejecting = True

    if not rejecting:
        return 0

    # We want to allow using this hook locally
    if hooktype == "pretxnchangegroup":
        return 1

    ui.write('This changeset would have been rejected!\n')
    return 0  # to fail not warn change to 1
