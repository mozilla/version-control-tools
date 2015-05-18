#!/usr/bin/env python
# Copyright (C) 2015 Mozilla Foundation
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""
This hook prevents non-comment changes to IDL interfaces without accompanying
UUID bumps.

The check can be skipped by adding 'IGNORE IDL' to the relevant commit messages
or 'a=release' to the tip commit message.
"""

import re
from mercurial.node import short

REJECT_MESSAGE = """
*************************** ERROR ***************************
Push rejected because the following IDL interfaces were
modified without changing the UUID:
  - %s

To update the UUID for all of the above interfaces and their
descendants, run:
  ./mach update-uuids %s

If you intentionally want to keep the current UUID, include
'IGNORE IDL' in the commit message.
*************************************************************

"""

# From mozilla-central/xpcom/idl-parser/xpidl.py.
IDL_MULTI_LINE_COMMENT_RE = re.compile(r'/\*(?s).*?\*/')
IDL_SINGLE_LINE_COMMENT_RE = re.compile(r'(?m)//.*?$')
IDL_UUID_PATTERN = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
IDL_IDENT_PATTERN = r'_?[A-Za-z][A-Za-z_0-9]*'

IDL_MATCH_ATTRIBUTE_LIST_AND_CAPTURE_UUID_PATTERN = \
    r'\[.*?\buuid\s*?\(\s*?(' + IDL_UUID_PATTERN + r')\s*?\).*?\]'

IDL_MATCH_INTERFACE_BODY_AND_CAPTURE_NAME_PATTERN = \
    r'\s+?interface\s+?(' + IDL_IDENT_PATTERN + r').*?\};'

ILD_RE = re.compile(
    r'(' + IDL_MATCH_ATTRIBUTE_LIST_AND_CAPTURE_UUID_PATTERN +
        IDL_MATCH_INTERFACE_BODY_AND_CAPTURE_NAME_PATTERN + r')',
    re.DOTALL | re.IGNORECASE)

def check_unbumped_idl_interfaces(old_idl, new_idl):
    """Compares the interfaces in old_idl and new_idl and returns the names
    of the interfaces that need a UUID bump. Any non-comment change in the
    interface body is considered to require a UUID bump.
    """
    def parse(idl):
        # Strip away comments first.
        idl = IDL_MULTI_LINE_COMMENT_RE.sub('', idl)
        idl = IDL_SINGLE_LINE_COMMENT_RE.sub('', idl)
        return dict((name, {'uuid': uuid, 'body': body})
                        for body, uuid, name in ILD_RE.findall(idl))
    old_interfaces = parse(old_idl)
    new_interfaces = parse(new_idl)
    return [x for x in new_interfaces
                if (x in old_interfaces and
                    new_interfaces[x]['uuid'] == old_interfaces[x]['uuid'] and
                    new_interfaces[x]['body'] != old_interfaces[x]['body'])]

def hook(ui, repo, hooktype, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    changesets = list(repo.changelog.revs(repo[node].rev()))
    description = repo.changectx(changesets[-1]).description()

    # Leave uplifts alone.
    if 'a=release' in description.lower():
        return 0

    unbumped_interfaces = []

    for rev in changesets:
        ctx = repo[rev]
        if 'IGNORE IDL' in ctx.description():
            continue

        if len(ctx.parents()) > 1:
            # Skip merge changesets.
            continue

        for path in ctx.files():
            if not path.endswith('.idl'):
                continue

            if path not in ctx:  # Deleted file
                continue

            fctx = ctx[path]
            if fctx.filerev() == 0:  # New file
                continue

            prev_fctx = fctx.filectx(fctx.filerev() - 1)
            unbumped_interfaces.extend([(x, short(ctx.node())) for x in
                check_unbumped_idl_interfaces(prev_fctx.data(), fctx.data())])

    if unbumped_interfaces:
        names_and_revs = sorted(name + ' in changeset ' + rev
                                    for name, rev in unbumped_interfaces)
        names = sorted(set(name for name, rev in unbumped_interfaces))
        ui.warn(REJECT_MESSAGE % ('\n  - '.join(names_and_revs),
                                  ' '.join(names)))
        return 1

    return 0
