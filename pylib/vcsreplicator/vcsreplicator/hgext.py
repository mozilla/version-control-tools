# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to write replication events into Kafka."""

from __future__ import absolute_import

import hashlib
import logging
import os
import re
import time

import kafka.client as kafkaclient
import kafka.common as kafkacommon
import vcsreplicator.producer as vcsrproducer

from mercurial.i18n import _
from mercurial import (
    cmdutil,
    commands,
    error,
    extensions,
    hg,
    util,
)

testedwith = '3.5'

cmdtable = {}
command = cmdutil.command(cmdtable)


def precommithook(ui, repo, **kwargs):
    # We could probably handle local commits. But our target audience is
    # server environments, where local commits shouldn't be happening.
    # All new changesets should be added through addchangegroup. Enforce
    # that.
    ui.warn(_('cannot commit to replicating repositories; push instead\n'))
    return True


def pretxnopenhook(ui, repo, **kwargs):
    """Verify replication log is working before starting transaction.

    It doesn't make sense to perform a lot of work only to find out that the
    replication log can not be written to. So we check replication log
    writability when we open transactions so we fail fast.
    """
    try:
        vcsrproducer.send_heartbeat(ui.replicationproducer,
                                    partition=repo.replicationpartition)
    except Exception:
        ui.warn('replication log not available; all writes disabled\n')
        return 1

    repo._replicationinfo = {
        'pushkey': [],
        'changegroup': False,
    }


def pushkeyhook(ui, repo, namespace=None, key=None, old=None, new=None,
                ret=None, **kwargs):
    """Records that a pushkey update occurred.

    Pushkey updates should always occur inside a transaction. We don't write
    the pushkey update to the log inside the transaction because the
    transaction could get rolled back. Instead, we record the details of the
    pushkey and write messages after the transaction has closed.
    """
    # TODO assert we're in a transaction.
    repo._replicationinfo['pushkey'].append(
        (namespace, key, old, new, ret))


def pretxnchangegrouphook(ui, repo, node=None, source=None, **kwargs):
    repo._replicationinfo['changegroup'] = True



def pretxnclosehook(ui, repo, **kwargs):
    try:
        vcsrproducer.send_heartbeat(ui.replicationproducer,
                                    repo.replicationpartition)
    except Exception:
        ui.warn('replication log not available; cannot close transaction\n')
        return True


def txnclosehook(ui, repo, **kwargs):
    # Only send messages if a changegroup isn't present. This is
    # because our changegroup message handler performs an `hg pull`,
    # which will pull in pushkey data automatically.
    if not repo._replicationinfo['changegroup']:
        sendpushkeymessages(ui, repo)


def changegrouphook(ui, repo, node=None, source=None, **kwargs):
    start = time.time()

    heads = set(repo.heads())
    pushnodes = []
    pushheads = []

    for rev in range(repo[node].rev(), len(repo)):
        ctx = repo[rev]

        pushnodes.append(ctx.hex())

        if ctx.node() in heads:
            pushheads.append(ctx.hex())

    vcsrproducer.record_hg_changegroup(ui.replicationproducer,
                                       repo.replicationwireprotopath,
                                       source,
                                       pushnodes,
                                       pushheads,
                                       partition=repo.replicationpartition)
    duration = time.time() - start
    ui.status(_('recorded changegroup in replication log in %.3fs\n') % duration)


def sendpushkeymessages(ui, repo):
    for namespace, key, old, new, ret in repo._replicationinfo['pushkey']:

        start = time.time()
        vcsrproducer.record_hg_pushkey(ui.replicationproducer,
                                       repo.replicationwireprotopath,
                                       namespace,
                                       key,
                                       old,
                                       new,
                                       ret,
                                       partition=repo.replicationpartition)
        duration = time.time() - start
        ui.status(_('recorded updates to %s in replication log in %.3fs\n') % (
                    namespace, duration))


def initcommand(orig, ui, dest, **opts):
    # Send a heartbeat before we create the repo to ensure the replication
    # system is online. This helps guard against us creating the repo
    # and replication being offline.
    producer = ui.replicationproducer
    # TODO this should ideally go to same partition as replication event.
    for partition in sorted(ui.replicationpartitions):
        vcsrproducer.send_heartbeat(producer, partition=partition)
        break

    res = orig(ui, dest=dest, **opts)

    # init aborts if the repo already existed or in case of error. So we
    # can only get here if we created a repo.
    path = os.path.normpath(os.path.abspath(os.path.expanduser(dest)))
    if not os.path.exists(path):
        raise util.Abort('could not find created repo at %s' % path)

    repo = hg.repository(ui, path)

    # TODO we should delete the repo if we can't write this message.
    vcsrproducer.record_new_hg_repo(producer, repo.replicationwireprotopath,
                                    partition=repo.replicationpartition)
    ui.status(_('(recorded repository creation in replication log)\n'))

    return res


@command('replicatehgrc', [], 'replicate the hgrc for this repository')
def replicatehgrc(ui, repo):
    """Replicate the hgrc for this repository.

    When called, the content of the hgrc file for this repository will be
    sent to the replication service. Downstream mirrors will apply that
    hgrc.

    This command should be called when the hgrc of the repository changes.
    """
    if repo.vfs.exists('hgrc'):
        content = repo.vfs.read('hgrc')
    else:
        content = None

    producer = ui.replicationproducer
    vcsrproducer.record_hgrc_update(producer, repo.replicationwireprotopath,
                                    content,
                                    partition=repo.replicationpartition)
    ui.status(_('recorded hgrc in replication log\n'))


@command('sendheartbeat', [],
         'send a heartbeat message to the replication system',
         norepo=True)
def sendheartbeat(ui):
    """Send a heartbeat message through the replication system.

    This is useful to see if the replication mechanism is writable.
    """
    try:
        for partition in ui.replicationpartitions:
            vcsrproducer.send_heartbeat(ui.replicationproducer,
                                        partition=partition)
    except kafkacommon.KafkaError as e:
        raise error.Abort('error sending heartbeat: %s' % e.message)

    ui.status(_('wrote heartbeat message into replication log\n'))


def extsetup(ui):
    extensions.wrapcommand(commands.table, 'init', initcommand)

    # Configure null handler for kafka.* loggers to prevent "No handlers could
    # be found" messages from creeping into output.
    kafkalogger = logging.getLogger('kafka')
    if not kafkalogger.handlers:
        kafkalogger.addHandler(logging.NullHandler())


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

    def havepartitionmap():
        for k, v in ui.configitems(section):
            if k.startswith('partitionmap.'):
                return True
        return False

    if role == 'producer':
        topic = ui.config(section, 'topic')
        if not topic:
            raise util.Abort('%s.topic config option not set' % section)
        partition = ui.configint(section, 'partition', -1)
        if partition == -1 and not havepartitionmap():
            raise util.Abort('%s.partition or %s.partitionmap.* config '
                             'options not set' % (section, section))
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

        def kafkaproducer(self, topic):
            """Obtain a Kafka producer for a topic.

            Uses some of the settings for ``replcationproducer`` but with a
            different topic.
            """
            client = kafkaclient.KafkaClient(hosts, client_id=clientid,
                                             timeout=timeout)
            return vcsrproducer.Producer(client, topic, 0, batch_send=False,
                                         req_acks=reqacks,
                                         ack_timeout=acktimeout)

        @property
        def replicationpartitionmap(self):
            pm = {}
            for k, v in self.configitems('replicationproducer'):
                if not k.startswith('partitionmap.'):
                    continue

                parts, expr = v.split(':', 1)
                parts = [int(x.strip()) for x in parts.split(',')]
                pm[k[len('partitionmap.'):]] = (parts, re.compile(expr))

            if not pm:
                explicit = self.configint('replicationproducer', 'partition', -1)
                if explicit == -1:
                    raise error.Abort(_('partitions not defined'))
                pm['0'] = (explicit, re.compile('.*'))

            return pm

        @property
        def replicationpartitions(self):
            s = set()
            for partitions, expr in self.replicationpartitionmap.values():
                s |= set(partitions)
            return s

    ui.__class__ = replicatingui


def reposetup(ui, repo):
    if not repo.local():
        return

    # TODO add support for only replicating repositories under certain paths.

    ui.setconfig('hooks', 'precommit.vcsreplicator', precommithook,
                 'vcsreplicator')
    ui.setconfig('hooks', 'pretxnopen.vcsreplicator', pretxnopenhook,
                 'vcsreplicator')
    ui.setconfig('hooks', 'pushkey.vcsreplicator', pushkeyhook,
                 'vcsreplicator')
    ui.setconfig('hooks', 'pretxnchangegroup.vcsreplicator',
                 pretxnchangegrouphook, 'vcsreplicator')
    ui.setconfig('hooks', 'pretxnclose.vcsreplicator', pretxnclosehook,
                 'vcsreplicator')
    ui.setconfig('hooks', 'txnclose.vcsreplicator', txnclosehook,
                 'vcsreplicator')
    ui.setconfig('hooks', 'changegroup.vcsreplicator', changegrouphook,
                 'vcsreplicator')

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

        @property
        def replicationpartition(self):
            """The partition to use when writing replication messages.

            The partition is derived from the repo's wire protocol path and
            an optional partition mapping declaration.
            """
            pm = self.ui.replicationpartitionmap
            path = self.replicationwireprotopath

            for k, (parts, expr) in sorted(pm.items()):
                if not expr.match(path):
                    continue

                # Hash path to determine bucket/partition.
                # This isn't used for cryptography, so MD5 is sufficient.
                h = hashlib.md5()
                h.update(path)
                i = int(h.hexdigest(), 16)
                offset = i % len(parts)
                return parts[offset]

            raise error.Abort(_('unable to map repo to partition'),
                              hint=_('define a partition map with a ".*" '
                                     'fallback'))

    repo.__class__ = replicatingrepo
