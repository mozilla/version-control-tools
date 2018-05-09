# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial import util
from mercurial.node import short
from mozautomation.commitparser import (
    parse_requal_reviewers,
    is_backout,
)

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner
)

IPC_PEERS = [
    dict(name='Andrew McCreight', nick=['mccr8'], email=['continuation@gmail.com']),
    dict(name='Ben Kelly', nick=['bkelly'], email=['bkelly@mozilla.com', 'ben@wanderview.com']),
    dict(name='Bill McCloskey', nick=['billm'], email=['billm@mozilla.com']),
    dict(name='David Anderson', nick=['dvander'], email=['danderson@mozilla.com', 'dvander@alliedmods.net']),
    dict(name='Jed David', nick=['jld'], email=['jld@mozilla.com']),
    dict(name='Kan-Ru Chen', nick=['kanru'], email=['kchen@mozilla.com', 'kanru@kanru.info']),
    dict(name='Nathan Froyd', nick=['froydnj'], email=['nfroyd@mozilla.com']),
]

MISSING_REVIEW = """
Changeset %s alters sync-messages.ini without IPC peer review.

Please, request review from either:
"""
for p in IPC_PEERS:
    MISSING_REVIEW += "  - {} (:{})\n".format(p['name'], p['nick'][0])


class SyncIPCCheck(PreTxnChangegroupCheck):
    """Changes to ipc/ipdl/sync-messages.ini requires IPC peer review."""
    @property
    def name(self):
        return 'ipcsync_check'

    def relevant(self):
        return self.repo_metadata['firefox_releasing']

    def pre(self, node):
        # Accept the entire push for code uplifts
        self.is_uplift = 'a=release' in self.repo['tip'].description().lower()

    def check(self, ctx):
        if self.is_uplift:
            return True

        # Ignore merge changesets
        if len(ctx.parents()) > 1:
            return True

        # Ignore backouts
        if is_backout(ctx.description()):
            return True

        # Ignore changes that don't touch sync-messages.ini
        ipc_files = [f for f in ctx.files()
                     if f == 'ipc/ipdl/sync-messages.ini']
        if not ipc_files:
            return True

        # Allow patches authored by peers
        if self._is_peer_email(util.email(ctx.user())):
            return True

        # Allow if reviewed by any peer
        requal = list(parse_requal_reviewers(ctx.description()))
        if any(self._is_peer_nick(nick) for nick in requal):
            return True

        # Reject
        print_banner(self.ui, 'error', MISSING_REVIEW % short(ctx.node()))
        return False

    def post_check(self):
        return True

    @staticmethod
    def _is_peer_email(email):
        email = email.lower()
        for peer in IPC_PEERS:
            if email in peer['email']:
                return True
        return False

    @staticmethod
    def _is_peer_nick(nick):
        nick = nick.lower()
        for peer in IPC_PEERS:
            if nick in peer['nick']:
                return True
        return False
