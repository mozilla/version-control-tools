# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to write replication events into Kafka."""

from __future__ import absolute_import

import contextlib
import hashlib
import logging
import os
import re
import sys
import syslog
import time
import traceback

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

testedwith = '3.6'

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
    with ui.kafkainteraction():
        try:
            repo.producerlog('PRETXNOPEN_HEARTBEATSENDING')
            vcsrproducer.send_heartbeat(ui.replicationproducer,
                                        partition=repo.replicationpartition)
            repo.producerlog('PRETXNOPEN_HEARTBEATSENT')
        except Exception:
            repo.producerlog('EXCEPTION', traceback.format_exc())
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
    repo._replicationinfo['pushkey'].append(
        (namespace, key, old, new, ret))


def pretxnchangegrouphook(ui, repo, node=None, source=None, **kwargs):
    # Record that a changegroup is part of the transaction. We only emit
    # events after transaction close. Set a variable to indicate we should
    # emit a changegroup event.
    repo._replicationinfo['changegroup'] = True


def pretxnclosehook(ui, repo, **kwargs):
    """Check for writeable replication log before transaction close.

    We perform one final check for replication log writeability immediately
    before the transaction closes. We'll abort the transaction if the
    replication log can't be written to.
    """
    with ui.kafkainteraction():
        try:
            repo.producerlog('PRETXNCLOSE_HEARTBEATSENDING')
            vcsrproducer.send_heartbeat(ui.replicationproducer,
                                        repo.replicationpartition)
            repo.producerlog('PRETXNCLOSE_HEARTBEATSENT')
        except Exception:
            repo.producerlog('EXCEPTION', traceback.format_exc())
            ui.warn('replication log not available; cannot close transaction\n')
            return True


def txnclosehook(ui, repo, **kwargs):
    # Only send messages if a changegroup isn't present. This is
    # because our changegroup message handler performs an `hg pull`,
    # which will pull in pushkey data automatically.
    if not repo._replicationinfo['changegroup']:
        sendpushkeymessages(ui, repo)


def changegrouphook(ui, repo, node=None, source=None, **kwargs):
    """Record replication events after a changegroup has been added."""
    start = time.time()

    heads = set(repo.heads())
    pushnodes = []
    pushheads = []

    for rev in range(repo[node].rev(), len(repo)):
        ctx = repo[rev]

        pushnodes.append(ctx.hex())

        if ctx.node() in heads:
            pushheads.append(ctx.hex())

    with ui.kafkainteraction():
        repo.producerlog('CHANGEGROUPHOOK_SENDING')
        vcsrproducer.record_hg_changegroup(ui.replicationproducer,
                                           repo.replicationwireprotopath,
                                           source,
                                           pushnodes,
                                           pushheads,
                                           partition=repo.replicationpartition)
        duration = time.time() - start
        repo.producerlog('CHANGEGROUPHOOK_SENT')
        ui.status(_('recorded changegroup in replication log in %.3fs\n') %
                    duration)


def sendpushkeymessages(ui, repo):
    """Send messages indicating updates to pushkey values."""
    for namespace, key, old, new, ret in repo._replicationinfo['pushkey']:
        with ui.kafkainteraction():
            repo.producerlog('PUSHKEY_SENDING')
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
            repo.producerlog('PUSHKEY_SENT')
            ui.status(_('recorded updates to %s in replication log in %.3fs\n') % (
                        namespace, duration))


# Wraps ``hg init`` to send a replication event.
def initcommand(orig, ui, dest, **opts):
    with ui.kafkainteraction():
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

    with ui.kafkainteraction():
        producer = ui.replicationproducer
        repo.producerlog('HGRC_SENDING')
        vcsrproducer.record_hgrc_update(producer, repo.replicationwireprotopath,
                                        content,
                                        partition=repo.replicationpartition)
        repo.producerlog('HGRC_SENT')

    ui.status(_('recorded hgrc in replication log\n'))


@command('sendheartbeat', [],
         'send a heartbeat message to the replication system',
         norepo=True)
def sendheartbeat(ui):
    """Send a heartbeat message through the replication system.

    This is useful to see if the replication mechanism is writable.
    """
    with ui.kafkainteraction():
        try:
            partitions = ui.replicationpartitions
            for partition in partitions:
                ui.status('sending heartbeat to partition %d\n' % partition)
                vcsrproducer.send_heartbeat(ui.replicationproducer,
                                            partition=partition)
        except kafkacommon.KafkaError as e:
            ui.producerlog('<unknown>', 'EXCEPTION', traceback.format_exc())
            raise error.Abort('error sending heartbeat: %s' % e.message)

    ui.status(_('wrote heartbeat message into %d partitions\n') %
            len(partitions))


@command('replicatesync', [], 'replicate this repository to mirrors')
def replicatecommand(ui, repo):
    """Tell mirrors to synchronize their copy of this repo.

    This is intended as a support command to be used to force replication.
    If the replication system is working as intended, it should not need to be
    used.
    """
    if repo.vfs.exists('hgrc'):
        hgrc = repo.vfs.read('hgrc')
    else:
        hgrc = None

    heads = [repo[h].hex() for h in repo.heads()]

    with ui.kafkainteraction():
        repo.producerlog('SYNC_SENDING')
        producer = ui.replicationproducer
        vcsrproducer.record_hg_repo_sync(producer, repo.replicationwireprotopath,
                                         hgrc, heads, repo.requirements,
                                         partition=repo.replicationpartition)
        repo.producerlog('SYNC_SENT')
    ui.status(_('wrote synchronization message into replication log\n'))


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
    hosts = ui.configlist('replicationproducer', 'hosts')
    if not hosts:
        raise util.Abort('replicationproducer.hosts config option not set')

    clientid = ui.config('replicationproducer', 'clientid')
    if not clientid:
        raise util.Abort('replicationproducer.clientid config option not set')

    timeout = ui.configint('replicationproducer', 'connecttimeout', 10)

    topic = ui.config('replicationproducer', 'topic')
    if not topic:
        raise util.Abort('replicationproducer.topic config option not set')

    def havepartitionmap():
        for k, v in ui.configitems('replicationproducer'):
            if k.startswith('partitionmap.'):
                return True
        return False

    if not havepartitionmap():
        raise util.Abort('replicationproducer.partitionmap.* config options not set')

    reqacks = ui.configint('replicationproducer', 'reqacks', default=999)
    if reqacks not in (-1, 0, 1):
        raise util.Abort('replicationproducer.reqacks must be set to -1, 0, or 1')

    acktimeout = ui.configint('replicationproducer', 'acktimeout')
    if not acktimeout:
        raise util.Abort('replicationproducer.acktimeout config option not set')

    class replicatingui(ui.__class__):
        """Custom ui class that provides access to replication primitives."""

        @property
        def replicationproducer(self):
            """Obtain a ``Producer`` instance to write to the replication log."""
            if not getattr(self, '_replicationproducer', None):
                client = kafkaclient.KafkaClient(hosts, client_id=clientid,
                                                 timeout=timeout)
                self._replicationproducer = vcsrproducer.Producer(
                    client, topic, batch_send=False,
                    req_acks=reqacks, ack_timeout=acktimeout)

            return self._replicationproducer

        @property
        def replicationpartitionmap(self):
            pm = {}
            for k, v in self.configitems('replicationproducer'):
                # Ignore unrelated options in this section.
                if not k.startswith('partitionmap.'):
                    continue

                parts, expr = v.split(':', 1)
                parts = [int(x.strip()) for x in parts.split(',')]
                pm[k[len('partitionmap.'):]] = (parts, re.compile(expr))

            if not pm:
                raise error.Abort(_('partitions not defined'))

            return pm

        @property
        def replicationpartitions(self):
            s = set()
            for partitions, expr in self.replicationpartitionmap.values():
                s |= set(partitions)
            return s

        @contextlib.contextmanager
        def kafkainteraction(self):
            """Perform interactions with Kafka with error handling.

            All interactions with Kafka should occur inside this context
            manager. Kafka exceptions will be caught and handled specially.
            """
            try:
                yield
            except kafkacommon.KafkaError as e:
                self.producerlog('<unknown>', 'KAFKA_EXCEPTION',
                        traceback.format_exc())
                raise

        def producerlog(self, repo, action, *args):
            """Write to the producer syslog facility."""
            ident = self.config('replicationproducer', 'syslogident', 'vcsreplicator')
            facility = self.config('replicationproducer', 'syslogfacility', 'LOG_LOCAL2')
            facility = getattr(syslog, facility)
            syslog.openlog(ident, 0, facility)

            if not isinstance(repo, str):
                repo = repo.replicationwireprotopath

            pre = '%s %s %s' % (os.environ.get('USER', '<unknown>'), repo, action)
            syslog.syslog(syslog.LOG_NOTICE, '%s %s' % (pre, ' '.join(args)))
            syslog.closelog()


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
        """Custom repository class providing access to replication primitives."""

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

        def producerlog(self, action, *args):
            return self.ui.producerlog(self, action, *args)

    repo.__class__ = replicatingrepo
