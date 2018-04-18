# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import abc
import re


RE_VALID_NAME = re.compile('^[a-zA-Z0-9_]+$')


def print_banner(ui, level, message):
    width = max(len(l) for l in message.splitlines())
    banner = [
        ' {} '.format(level.upper()).center(width, '*'),
        message.strip(),
        '*' * width,
    ]
    ui.write('\n' + '\n'.join(banner) + '\n\n')


class PreTxnChangegroupCheck(object):
    """A check that operates as a pretxnchangegroup hook.

    A method is called for every changeset as part of the transaction.

    A method is also called once all changesets have been examined. This allows
    each changeset invocation to set state which is examined once all changesets
    have been examined.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, ui, repo, info):
        if not RE_VALID_NAME.match(self.name):
            raise Exception('check name is invalid: %s' % self.name)

        self.ui = ui
        self.repo = repo
        self.repo_metadata = info

    @abc.abstractproperty
    def name(self):
        """Name of this check.

        This is used to facilitate force enabling or disabling the check on a
        per-repo basis. It may also be displayed in logging or user output.
        """

    @abc.abstractmethod
    def relevant(self):
        """Allows checks to declare if they are relevant.

        Implementations can look at the repo or its metadata to see if they
        should be run.

        Returns True if the check should run. False otherwise.

        The return value of this method is tightly validated to help prevent
        logic bugs.
        """

    @abc.abstractmethod
    def pre(self, node):
        """Called once before any changesets are examined.

        Allows derived classes to set additional instance state without having
        to call parent methods.

        `node` - the first changeset in the group that was added (as per
                 pretxnchangegroup).

        Return value is ignored.
        """

    @abc.abstractmethod
    def check(self, ctx):
        """Verifies a single changeset.

        `ctx` - changectx object.

        Returns True if the check passes. False otherwise.
        """

    @abc.abstractmethod
    def post_check(self):
        """Called after all changesets have been checked.

        If the check gathers state during per-changeset invocations and needs
        to consult that state after all changesets are observed, it should do
        so here.

        Returns True if the check passes. False otherwise.
        """


class ChangeGroupCheck(object):
    """A check that operates as a changegroup hook."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, ui, repo, info):
        if not RE_VALID_NAME.match(self.name):
            raise Exception('check name is invalid: %s' % self.name)

        self.ui = ui
        self.repo = repo
        self.repo_metadata = info

    @abc.abstractproperty
    def name(self):
        """Name of this check.

        This is used to facilitate force enabling or disabling the check on a
        per-repo basis. It may also be displayed in logging or user output.
        """

    @abc.abstractmethod
    def relevant(self):
        """Allows checks to declare if they are relevant.

        Implementations can look at the repo or its metadata to see if they
        should be run.

        Returns True if the check should run. False otherwise.

        The return value of this method is tightly validated to help prevent
        logic bugs.
        """

    @abc.abstractmethod
    def check(self, **kwargs):
        """Verifies a single changeset.

        **kwargs contains additional args passed into changegroup.

        Returns True if the check passes. False otherwise.
        """

