# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Utility functions for performing various Git functionality."""

from __future__ import absolute_import, unicode_literals

import subprocess


def update_git_refs(repo, reason, *actions):
    """Update Git refs via reflog writes.

    Accepts a ``dulwich.repo.Repo``, a bytes ``reason`` describing why this
    was done, and 1 or more tuples describing the update to perform. Tuples
    have the form:

    ('update', ref, new_id, old_id)
    ('create', ref, id)
    """
    assert isinstance(reason, bytes)

    commands = []
    for action in actions:
        if action[0] == 'update':
            # Destructing will raise if length isn't correct, which is
            # desired for error checking.
            cmd, ref, new, old = action
            commands.append(b'update %s\0%s\0%s' % (ref, new, old))
        elif action[0] == 'create':
            cmd, ref, new = action
            commands.append(b'create %s\0%s' % (ref, new))
        else:
            raise Exception('unhandled action %s' % action[0])

    p = subprocess.Popen([b'git', b'update-ref',
                          b'--create-reflog', b'-m', reason,
                          b'--stdin', b'-z'],
                         stdin=subprocess.PIPE,
                         cwd=repo.path)
    p.stdin.write(b'\0'.join(commands))
    p.stdin.close()
    res = p.wait()
    # TODO could use a more rich exception type that captures output.
    if res:
        raise Exception('failed to update git refs')
