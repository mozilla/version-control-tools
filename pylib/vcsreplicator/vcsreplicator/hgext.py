# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to write replication events into Kafka."""

from __future__ import absolute_import

import os

import kafka.client as kafkaclient
import vcsreplicator.producer as vcsrproducer

from mercurial.i18n import _
from mercurial import (
    commands,
    extensions,
    hg,
    util,
)

testedwith = '3.5'


def initcommand(orig, ui, dest, **opts):
    # Send a heartbeat before we create the repo to ensure the replication
    # system is online. This helps guard against us creating the repo
    # and replication being offline.
    producer = ui.replicationproducer
    vcsrproducer.send_heartbeat(producer)

    res = orig(ui, dest=dest, **opts)

    # init aborts if the repo already existed or in case of error. So we
    # can only get here if we created a repo.
    path = os.path.normpath(os.path.abspath(os.path.expanduser(dest)))
    if not os.path.exists(path):
        raise util.Abort('could not find created repo at %s' % path)

    repo = hg.repository(ui, path)

    # TODO we should delete the repo if we can't write this message.
    vcsrproducer.record_new_hg_repo(producer, repo.replicationwireprotopath)
    ui.status(_('(recorded repository creation in replication log)\n'))

    return res


def extsetup(ui):
    extensions.wrapcommand(commands.table, 'init', initcommand)


def uisetup(ui):
    # We assume that if the extension is loaded that we want replication
    # support enabled. Validate required config options are present.
    role = ui.config('replication', 'role')
    if not role:
        raise util.Abort('replication.role config option not set')

    if role not in ('producer', 'consumer'):
        raise util.Abort('unsupported value for replication.role: %s' % role,
                         hint='expected "producer" or "consumer"')

    section = 'replication%s' % role
    hosts = ui.configlist(section, 'hosts')
    if not hosts:
        raise util.Abort('%s.hosts config option not set' % section)
    clientid = ui.config(section, 'clientid')
    if not clientid:
        raise util.Abort('%s.clientid config option not set' % section)
    timeout = ui.configint(section, 'connecttimeout', 10)

    if role == 'producer':
        topic = ui.config(section, 'topic')
        if not topic:
            raise util.Abort('%s.topic config option not set' % section)
        partition = ui.configint(section, 'partition', -1)
        if partition == -1:
            raise util.Abort('%s.partition config option not set' % section)
        reqacks = ui.configint(section, 'reqacks', default=999)
        if reqacks not in (-1, 0, 1):
            raise util.Abort('%s.reqacks must be set to -1, 0, or 1' % section)
        acktimeout = ui.configint(section, 'acktimeout')
        if not acktimeout:
            raise util.Abort('%s.acktimeout config option not set' % section)

    class replicatingui(ui.__class__):
        @property
        def replicationproducer(self):
            if not getattr(self, '_replicationproducer', None):
                client = kafkaclient.KafkaClient(hosts, client_id=clientid,
                                                 timeout=timeout)
                self._replicationproducer = vcsrproducer.Producer(
                    client, topic, partition, batch_send=False,
                    req_acks=reqacks, ack_timeout=acktimeout)

            return self._replicationproducer

    ui.__class__ = replicatingui


def reposetup(ui, repo):
    if not repo.local():
        return

    # TODO add support for only replicating repositories under certain paths.

    class replicatingrepo(repo.__class__):
        @property
        def replicationwireprotopath(self):
            """Return the path to this repo as it is represented over wire.

            By setting entries in the [replicationpathrewrites] section, you can
            effectively normalize filesystem paths to a portable representation.
            For example, say all Mercurial repositories are stored in
            ``/repos/hg/`` on the local filesystem. You could create a rewrite
            rule as follows:

               [replicationpathrewrites]
               /repos/hg/ = {hg}/

            Over the wire, a local path such as ``/repos/hg/my-repo`` would be
            normalized to ``{hg}/my-repo``.

            Then on the consumer, you could design the opposite to map the
            repository to a different filesystem path. e.g.:

               [replicationpathrewrites]
               {hg}/ = /mirror/hg/

            The consumer would then expand the path to ``/mirror/hg/my-repo``.

            Matches are case insensitive but rewrites are case preserving.
            """
            lower = self.root.lower()
            for source, dest in self.ui.configitems('replicationpathrewrites'):
                if lower.startswith(source):
                    return dest + self.root[len(source):]

            return self.root

    repo.__class__ = replicatingrepo
