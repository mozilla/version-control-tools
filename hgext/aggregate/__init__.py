# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Aggregate multiple Mercurial repositories into a local repository.

This extension is used to aggregate (pull) the contents of multiple
remotes into a local repository. It is essentially a glorified wrapper
around invoking ``hg pull`` multiple times.

Avoiding Excessive Locking
==========================

By default, Mercurial will hold a lock around the entire ``pull()`` operation.
This includes discovery, which may be time-consuming.

This extension changes behavior such that discovery occurs outside of the lock
and no lock is taken if there are no incoming changesets.
"""

import contextlib
import io

from mercurial import (
    cmdutil,
    exchange,
    hg,
)
from mercurial.error import (
    Abort,
)

testedwith = '3.2 3.3'

cmdtable = {}
command = cmdutil.command(cmdtable)

class NoIncomingError(Exception):
    """Indicates no incoming changes from remote."""

@contextlib.contextmanager
def capturehgoutput(ui):
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    oldout = ui.fout
    olderr = ui.ferr
    try:
        ui.fout = stdout
        ui.ferr = stderr

        yield stdout, stderr

    finally:
        ui.fout = oldout
        ui.ferr = olderr

@command('aggregate', [], 'aggregate remote repositories')
def aggregate(ui, repo, **opts):
    """Aggregate remote repositories.

    This is like ``hg pull`` except it pulls from multiple remotes and does the
    pulling in such a way to avoid excessive repository locking.
    """
    aggregate_once(ui, repo)

def aggregate_once(ui, repo):
    oldlen = len(repo)
    pullcount = 0

    for name, url in ui.configitems('paths'):
        remote = hg.peer(repo, {}, url)
        try:
            exchange.pull(repo, remote)
            pullcount += 1
        except NoIncomingError:
            pass

    newlen = len(repo)
    delta = newlen - oldlen
    if delta:
        ui.status('aggregated %d changesets from %d repos\n' % (delta, pullcount))
    else:
        ui.status('no changesets aggregated\n')

def pulldiscoverychangegroup(pullop):
    """Wraps exchange._pulldiscoverychangegroup to no-op.

    Our custom ``exchange.pulloperation`` performs discovery outside of the
    lock. To avoid double discovery, we make the original function no-op.
    """
    if pullop.common is None:
        raise Abort('assertion failed: discovery should have executed already')

    return

def extsetup(ui):
    exchange.pulldiscoverymapping['changegroup'] = pulldiscoverychangegroup

    class aggregatepulloperation(exchange.pulloperation):
        def __init__(self, repo, remote, *args, **kwargs):
            super(aggregatepulloperation, self).__init__(repo, remote, *args, **kwargs)

            with capturehgoutput(repo.ui):
                # Do discovery immediately, before the lock is acquired.
                exchange._pulldiscoverychangegroup(self)

            # Assumption: we don't care about anything in listkeys.
            if not self.fetch:
                raise NoIncomingError()

            repo.ui.status('pulling from %s\n' % remote.url())

    exchange.pulloperation = aggregatepulloperation
