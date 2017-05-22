# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Utility functions for performing various Git functionality."""

from __future__ import absolute_import, unicode_literals

import logging
import os
import pipes
import subprocess

logger = logging.getLogger(__name__)


class GitCommand(object):
    """Helper class for running git commands"""

    def __init__(self, repo_path, secret=None):
        """
        :param repo_path: the full path to the git repo.
        :param logger: if set the command executed will be logged with
                       level info.
        :param secret: this string will be replaced with 'xxx' when logging.
        """
        self.repo_path = repo_path
        self.logger = logger
        self.secret = secret

    def cmd(self, *command):
        """ Run the specified command with git.

        eg. git.cmd('status', '--short')
        """
        assert command and len(command)
        command = ['git'] + list(command)
        if self.logger:
            command_str = ' '.join(map(pipes.quote, command))
            if self.secret:
                command_str = command_str.replace(self.secret, 'xxx')
            self.logger.info('$ %s' % command_str)
        subprocess.check_call(command, cwd=self.repo_path)

    def get(self, *command):
        """ Run the specified command with git and return the result.

        eg. diff = git.cmd('diff', '--no-color')
        """
        assert command and len(command)
        command = ['git'] + list(command)
        return subprocess.check_output(command, cwd=self.repo_path)


def setup_local_clone(path, url, git=None):
    git = git or GitCommand(path)

    if not os.path.exists(path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        logger.info('cloning %s to %s' % (url, path))
        git.cmd('clone', url, path)


def update_git_refs(repo, reason, *actions):
    """Update Git refs via reflog writes.

    Accepts a ``dulwich.repo.Repo``, a bytes ``reason`` describing why this
    was done, and 1 or more tuples describing the update to perform. Tuples
    have the form:

    ('update', ref, new_id, old_id)
    ('create', ref, id)
    ('delete', ref, old_id)
    ('force-delete', ref)
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
        elif action[0] == 'delete':
            cmd, ref, old = action
            commands.append(b'delete %s\0%s' % (ref, old))
        elif action[0] == 'force-delete':
            cmd, ref = action
            commands.append(b'delete %s\0' % ref)
        else:
            raise Exception('unhandled action %s' % action[0])

    p = subprocess.Popen([b'git', b'update-ref',
                          b'--create-reflog', b'-m', reason,
                          b'--stdin', b'-z'],
                         stdin=subprocess.PIPE,
                         cwd=repo.path)
    for command in commands:
        p.stdin.write(command)
        p.stdin.write(b'\0')
    p.stdin.close()
    res = p.wait()
    # TODO could use a more rich exception type that captures output.
    if res:
        raise Exception('failed to update git refs')
