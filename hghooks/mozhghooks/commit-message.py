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
from mercurial.node import short
from mercurial import (
    pycompat,
)
from mozautomation import commitparser

INVALID_REVIEW_FLAG_RE = re.compile(rb"[\s.;]r\?(?:\w|$)")

goodMessage = [
    re.compile(x, re.I)
    for x in [
        rb"bug [0-9]+",
        rb"no bug",
        rb"^(back(ing|ed)?\s+out|backout).*(\s+|\:)[0-9a-f]{12}",
        rb"^(revert(ed|ing)?).*(\s+|\:)[0-9a-f]{12}",
        rb"^add(ed|ing)? tag",
    ]
]

VENDORED_PATHS = (b"servo/",)


def is_vendor_ctx(ctx):
    # Other hooks should ensure that only certain users can change
    # vendored paths.
    if not any(f.startswith(VENDORED_PATHS) for f in ctx.files()):
        return False

    return True


def is_good_message(ui, c):
    def message(fmt):
        formatted_fmt = fmt % {b"rev": c.hex()[:12]}
        ui.write(
            b"\n\n"
            b"************************** ERROR ****************************\n"
            b"%s\n%s\n%s\n"
            b"*************************************************************\n"
            b"\n\n" % (formatted_fmt, c.user(), c.description())
        )

    desc = c.description()
    firstline = desc.splitlines()[0]

    # Ensure backout commit descriptions are well formed.
    if commitparser.is_backout(desc):
        try:
            if not commitparser.parse_backouts(desc, strict=True):
                raise ValueError("Rev %(rev)s has malformed backout message.")
            nodes, bugs = commitparser.parse_backouts(desc, strict=True)
            if not nodes:
                raise ValueError("Rev %(rev)s is missing backed out revisions.")
        except ValueError as e:
            # Reject invalid backout messages on vendored paths, warn otherwise.
            if is_vendor_ctx(c):
                message(pycompat.bytestr(e))
                return False
            ui.write(b"Warning: %s\n" % (pycompat.bytestr(e) % {b"rev": c.hex()[:12]}))

    # Vendored merges must reference source revisions.
    if b"Source-Revision: " in desc and is_vendor_ctx(c):
        ui.write(
            b"(%s looks like a vendoring change; ignoring commit message "
            b"hook)\n" % short(c.node())
        )
        return True

    if c.user() in [b"ffxbld", b"seabld", b"tbirdbld", b"cltbld"]:
        return True

    # Match against [PATCH] and [PATCH n/m]
    if b"[PATCH" in desc:
        message(
            b'Rev %(rev)s contains git-format-patch "[PATCH]" cruft. Use '
            b"git-format-patch -k to avoid this."
        )
        return False

    if INVALID_REVIEW_FLAG_RE.search(firstline):
        message(
            b"Rev %(rev)s contains 'r?' in the commit message. Please use "
            b"'r=' instead."
        )
        return False

    desc_lower = desc.lower()
    if desc_lower.startswith(b"wip:"):
        message(b"Rev %(rev)s seems to be marked as WIP.")
        return False

    for r in goodMessage:
        if r.search(firstline):
            return True

    if desc_lower.startswith((b"merge", b"merging", b"automated merge")):
        if len(c.parents()) == 2:
            return True
        else:
            message(
                b"Rev %(rev)s claims to be a merge, but it has only one parent."
            )
            return False

    if desc_lower.startswith((b"back", b"revert")):
        # Purposely ambiguous: it's ok to say "backed out rev N" or
        # "reverted to rev N-1"
        message(b"Backout rev %(rev)s needs a bug number or a rev id.")
    else:
        message(b'Rev %(rev)s needs "Bug N" or "No bug" in the commit message.')

    return False


def hook(ui, repo, node, hooktype, source=None, **kwargs):
    if source in (b"pull", b"strip"):
        return 0

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo[node].rev()
    tip = repo[b"tip"].rev()
    rejecting = False

    for i in reversed(range(rev, tip + 1)):
        c = repo[i]

        if b"IGNORE BAD COMMIT MESSAGES" in c.description():
            # Ignore commit messages for all earlier revs in this push.
            break

        if not is_good_message(ui, c):
            # Keep looping so the pusher sees all commits they need to fix.
            rejecting = True

    if not rejecting:
        return 0

    # We want to allow using this hook locally
    if hooktype == b"pretxnchangegroup":
        return 1

    ui.write(b"This changeset would have been rejected!\n")
    return 0  # to fail not warn change to 1
