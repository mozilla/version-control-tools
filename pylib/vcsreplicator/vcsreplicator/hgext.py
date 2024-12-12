# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to write replication events into Kafka."""

from __future__ import absolute_import

import contextlib
import functools
import hashlib
import logging
import os
import re
import shutil
import sys
import syslog
import time
import traceback

from vcsreplicator import (
    commoncommands,
    producer as vcsrproducer,
)

from mercurial.i18n import _
from mercurial.node import hex
from mercurial import (
    bundle2,
    cmdutil,
    commands,
    configitems,
    demandimport,
    error,
    extensions,
    hg,
    obsolete,
    phases,
    policy,
    pycompat,
    registrar,
    util,
    wireprotov1server,
)


with demandimport.deactivated():
    from kafka import SimpleClient
    import kafka.common as kafkacommon

    # kafka.codec does module sniffing via imports. Import it explicitly
    # to force it to import now.
    import kafka.codec as kafkacodec

base85 = policy.importmod("base85")

testedwith = b"4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.2 5.3 5.4 5.5"

cmdtable = {}

command = registrar.command(cmdtable)

# Register `hg mozrepohash` with the command registrar
command(
    b"mozrepohash",
    [
        (b"", b"no-raw", False, b"skip hashing raw files"),
    ]
    + cmdutil.formatteropts,
)(commoncommands.mozrepohash)

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b"replicationproducer", b"hosts", default=[])
configitem(b"replicationproducer", b"clientid", default=None)
configitem(
    b"replicationproducer", b"connecttimeout", default=configitems.dynamicdefault
)
configitem(b"replicationproducer", b"topic", default=None)
configitem(b"replicationproducer", b"reqacks", default=configitems.dynamicdefault)
configitem(b"replicationproducer", b"acktimeout", default=0)
configitem(b"replicationproducer", b"producermap.*", default=configitems.dynamicdefault)
configitem(b"replication", b"unfiltereduser", default=None)


_ORIG_PHASE_HEADS_HANDLER = bundle2.parthandlermapping.get(b"phase-heads")


def precommithook(ui, repo, **kwargs):
    # We could probably handle local commits. But our target audience is
    # server environments, where local commits shouldn't be happening.
    # All new changesets should be added through addchangegroup. Enforce
    # that.
    ui.warn(_(b"cannot commit to replicating repositories; push instead\n"))
    return True


def pretxnopenhook(ui, repo, **kwargs):
    """Verify replication log is working before starting transaction.

    It doesn't make sense to perform a lot of work only to find out that the
    replication log can not be written to. So we check replication log
    writability when we open transactions so we fail fast.
    """
    with ui.kafkainteraction():
        try:
            repo.producerlog("PRETXNOPEN_HEARTBEATSENDING")
            vcsrproducer.send_heartbeat(
                ui.replicationproducer, partition=repo.replicationpartition
            )
            repo.producerlog("PRETXNOPEN_HEARTBEATSENT")
        except Exception as e:
            repo.producerlog("EXCEPTION", "%s: %s" % (e, traceback.format_exc()))
            ui.warn(b"replication log not available; all writes disabled\n")
            return 1

    repo._replicationinfo = {
        "pushkey": [],
        "changegroup": False,
        "obsolescence": {},
        # Stuff a copy of served heads so we can determine after close
        # whether they changed and we need to write a message.
        "pre_served_heads": repo.filtered(b"served").heads(),
    }


def pushkeyhook(
    ui, repo, namespace=None, key=None, old=None, new=None, ret=None, **kwargs
):
    """Records that a pushkey update occurred."""
    # The way pushkey updates work with regards to transactions is wonky.
    # repo.pushkey() is the main function called to perform pushkey updates.
    # It's what calls hooks (like this function). However, it does not
    # necessarily have a transaction opened when called. This means that
    # there may not be an active transaction when we're called! However,
    # the low-level pushkey namespace implementations (e.g. phases.pushphase())
    # do obtain a transaction. So a transaction is involved with pushkey
    # updates.
    #
    # We don't write messages into the replication log until a transaction
    # has closed. Otherwise, transaction rollback could result in downstream
    # consumers seeing updates they shouldn't. So, we queue our messages for
    # writing. They will get flushed when the transaction associated with
    # the low-level pushkey update completes.
    #
    # Obsolescence markers are handled via a separate mechanism. So ignore
    # them.

    # Not all pushkey namespaces are consistent in their internal return
    # value. Some use int. Others bool. We want to be consistent in the type
    # written to the replication log. And int is more expressive. So we use
    # that.
    if isinstance(ret, bool):
        ret = 0 if ret else 1
    elif ret is None:
        ret = 0

    if namespace == b"obsolescence":
        return

    repo._replicationinfo["pushkey"].append(
        (
            pycompat.sysstr(namespace),
            pycompat.sysstr(key),
            pycompat.sysstr(old),
            pycompat.sysstr(new),
            ret,
        )
    )


# This is a handler for the bundle2 phase-heads part. The prepushkey/pushkey
# hooks don't run for phases when phases are updated via bundle2. This is
# arguably an upstream bug. So we install a custom part handler to record the
# equivalent data in the replication log as a pushkey message.
def phase_heads_handler(op, inpart):
    # If the push has changegroup data, we'll generate a changegroup replication
    # message and the corresponding `hg pull` will update phases automatically.
    # So we don't need to do anything special for replication.
    if (
        not util.safehasattr(op.repo, r"_replicationinfo")
        or op.repo._replicationinfo[r"changegroup"]
    ):
        return _ORIG_PHASE_HEADS_HANDLER(op, inpart)

    # Else this looks like a push without a changegroup. (A phase only push.)
    # We monkeypatch the function for handling phase updates to record what
    # changes were made. Then we convert the changes into pushkey messages.

    # We make assumptions later that we only update from the draft phase. Double
    # check that the source repo doesn't have any secret, etc phase roots.
    seen_phases = set(
        phase
        for phase, roots in op.repo.unfiltered()._phasecache._phaseroots.items()
        if roots
    )
    supported_phases = {phases.public, phases.draft}

    if seen_phases - supported_phases:
        raise error.Abort(_(b"only draft and public phases are supported"))

    moves = {}

    def wrapped_advanceboundary(orig, repo, tr, targetphase, nodes):
        if targetphase in moves:
            raise error.ProgrammingError(b"already handled phase %r" % targetphase)

        if targetphase not in supported_phases:
            raise error.Abort(_(b"only draft and public phases are supported"))

        moves[targetphase] = nodes

        return orig(repo, tr, targetphase, nodes)

    with extensions.wrappedfunction(
        phases, "advanceboundary", wrapped_advanceboundary
    ):
        _ORIG_PHASE_HEADS_HANDLER(op, inpart)

    for phase, nodes in sorted(moves.items()):
        for node in nodes:
            op.repo._replicationinfo["pushkey"].append(
                (
                    "phases",
                    pycompat.sysstr(hex(node)),
                    "%d" % phases.draft,
                    "%d" % phase,
                    0,
                )
            )


def pretxnchangegrouphook(ui, repo, node=None, source=None, **kwargs):
    # Record that a changegroup is part of the transaction. We only emit
    # events after transaction close. Set a variable to indicate we should
    # emit a changegroup event.
    repo._replicationinfo["changegroup"] = True


def pretxnclosehook(ui, repo, **kwargs):
    """Check for writeable replication log before transaction close.

    We perform one final check for replication log writeability immediately
    before the transaction closes. We'll abort the transaction if the
    replication log can't be written to.
    """
    with ui.kafkainteraction():
        try:
            repo.producerlog("PRETXNCLOSE_HEARTBEATSENDING")
            vcsrproducer.send_heartbeat(
                ui.replicationproducer, repo.replicationpartition
            )
            repo.producerlog("PRETXNCLOSE_HEARTBEATSENT")
        except Exception as e:
            repo.producerlog("EXCEPTION", "%s: %s" % (e, traceback.format_exc()))
            ui.warn(b"replication log not available; cannot close transaction\n")
            return True

    # If our set of served heads changed in the course of this transaction,
    # schedule the writing of a message to reflect this. The message can be
    # used by downstream consumers to influence which heads are exposed to
    # clients.
    heads = repo.filtered(b"served").heads()

    if heads != repo._replicationinfo["pre_served_heads"]:
        tr = repo.currenttransaction()
        tr.addpostclose(
            b"vcsreplicator-record-heads-change",
            lambda tr: repo._afterlock(functools.partial(sendheadsmessage, ui, repo)),
        )


def txnclosehook(ui, repo, **kwargs):
    # Obtain obsolescence markers added as part of the transaction. These
    # will be sent as pushkey messages later.
    obscount = int(kwargs.get("new_obsmarkers", "0"))
    if obscount:
        markers = repo.obsstore._all[-obscount:]
        repo._replicationinfo["obsolescence"] = obsolete._pushkeyescape(markers)

    # Only send messages if a changegroup isn't present. This is
    # because our changegroup message handler performs an `hg pull`,
    # which will pull in pushkey data automatically.
    if not repo._replicationinfo["changegroup"]:
        sendpushkeymessages(ui, repo)

        # Obsolescence markers may not arrive via pushkey and may not be
        # recorded via the pushkey hooks mechanism. So send them manually.
        #
        # We send these markers during the changegroup hook if it fires,
        # which should be after this hook.
        for key, value in sorted(repo._replicationinfo["obsolescence"].items()):
            sendpushkeymessage(
                ui,
                repo,
                "obsolete",
                pycompat.sysstr(key),
                "",
                pycompat.sysstr(value),
                0,
            )


def changegrouphook(ui, repo, node=None, source=None, **kwargs):
    """Record replication events after a changegroup has been added."""
    start = time.time()

    heads = set(repo.heads())
    pushnodes = []
    pushheads = []

    for rev in range(repo[node].rev(), len(repo)):
        ctx = repo[rev]

        pushnodes.append(pycompat.sysstr(ctx.hex()))

        if ctx.node() in heads:
            pushheads.append(pycompat.sysstr(ctx.hex()))

    with ui.kafkainteraction():
        repo.producerlog("CHANGEGROUPHOOK_SENDING")
        vcsrproducer.record_hg_changegroup(
            ui.replicationproducer,
            repo.replicationwireprotopath,
            pycompat.sysstr(source),
            pushnodes,
            pushheads,
            partition=repo.replicationpartition,
        )
        duration = time.time() - start
        repo.producerlog("CHANGEGROUPHOOK_SENT")
        ui.status(_(b"recorded changegroup in replication log in %.3fs\n") % duration)

        for key, value in sorted(repo._replicationinfo["obsolescence"].items()):
            sendpushkeymessage(
                ui,
                repo,
                "obsolete",
                pycompat.sysstr(key),
                "",
                pycompat.sysstr(value),
                0,
            )


def sendpushkeymessages(ui, repo):
    """Send messages indicating updates to pushkey values."""
    for namespace, key, old, new, ret in repo._replicationinfo["pushkey"]:
        sendpushkeymessage(ui, repo, namespace, key, old, new, ret)


def sendpushkeymessage(ui, repo, namespace, key, old, new, ret):
    """Send a pushkey replication message."""
    with ui.kafkainteraction():
        repo.producerlog("PUSHKEY_SENDING")
        start = time.time()
        vcsrproducer.record_hg_pushkey(
            ui.replicationproducer,
            repo.replicationwireprotopath,
            namespace,
            key,
            old,
            new,
            ret,
            partition=repo.replicationpartition,
        )
        duration = time.time() - start
        repo.producerlog("PUSHKEY_SENT")
        ui.status(
            _(b"recorded updates to %s in replication log in %.3fs\n")
            % (pycompat.bytestr(namespace), duration)
        )


def yield_encoded_requirements(requirements):
    for r in requirements:
        yield pycompat.sysstr(r)


def sendreposyncmessage(ui, repo, bootstrap=False):
    """Send a message to perform a full repository sync."""
    if repo.vfs.exists(b"hgrc"):
        hgrc = repo.vfs.read(b"hgrc").decode("utf-8", "surrogatepass")
    else:
        hgrc = None

    heads = [pycompat.sysstr(repo[h].hex()) for h in repo.heads()]

    with ui.kafkainteraction():
        repo.producerlog("SYNC_SENDING")
        producer = ui.replicationproducer

        requirements = yield_encoded_requirements(repo.requirements)

        vcsrproducer.record_hg_repo_sync(
            producer,
            repo.replicationwireprotopath,
            hgrc,
            heads,
            requirements,
            partition=repo.replicationpartition,
            bootstrap=bootstrap,
        )
        repo.producerlog("SYNC_SENT")


def sendheadsmessage(ui, repo, success=True):
    """Repo-unlock callback function to send a message
    notifying callers about the new heads

    TRACKING hg53: make `success` default to `False`
    """
    # Don't send the heads message if the unlock was not a success
    if not success:
        return

    heads = [pycompat.sysstr(hex(n)) for n in repo.filtered(b"served").heads()]

    # Pull numeric push ID from the pushlog extensions, if available.
    if util.safehasattr(repo, "pushlog"):
        last_push_id = repo.pushlog.lastpushid()
    else:
        last_push_id = None

    with ui.kafkainteraction():
        repo.producerlog("HEADS_SENDING")
        producer = ui.replicationproducer
        vcsrproducer.record_hg_repo_heads(
            producer,
            repo.replicationwireprotopath,
            heads,
            last_push_id,
            partition=repo.replicationpartition,
        )

        repo.producerlog("HEADS_SENT")


def sendrepodeletemessage(ui, repo):
    """Send a message to delete a repository."""
    with ui.kafkainteraction():
        repo.producerlog("DELETE_SENDING")
        producer = ui.replicationproducer
        vcsrproducer.record_hg_repo_delete(
            producer, repo.replicationwireprotopath, partition=repo.replicationpartition
        )
        repo.producerlog("DELETE_SENT")


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
            raise error.Abort(b"could not find created repo at %s" % path)

        repo = hg.repository(ui, path)
        gd = b"generaldelta" in repo.requirements

        # TODO we should delete the repo if we can't write this message.
        vcsrproducer.record_new_hg_repo(
            producer,
            repo.replicationwireprotopath,
            partition=repo.replicationpartition,
            generaldelta=gd,
        )
        ui.status(_(b"(recorded repository creation in replication log)\n"))

        return res


@command(b"replicatehgrc", [], b"replicate the hgrc for this repository")
def replicatehgrc(ui, repo):
    """Replicate the hgrc for this repository.

    When called, the content of the hgrc file for this repository will be
    sent to the replication service. Downstream mirrors will apply that
    hgrc.

    This command should be called when the hgrc of the repository changes.
    """
    if repo.vfs.exists(b"hgrc"):
        content = repo.vfs.read(b"hgrc").decode("utf-8", "surrogatepass")
    else:
        content = None

    with ui.kafkainteraction():
        producer = ui.replicationproducer
        repo.producerlog("HGRC_SENDING")
        vcsrproducer.record_hgrc_update(
            producer,
            repo.replicationwireprotopath,
            content,
            partition=repo.replicationpartition,
        )
        repo.producerlog("HGRC_SENT")

    ui.status(_(b"recorded hgrc in replication log\n"))


@command(
    b"sendheartbeat",
    [],
    b"send a heartbeat message to the replication system",
    norepo=True,
)
def sendheartbeat(ui):
    """Send a heartbeat message through the replication system.

    This is useful to see if the replication mechanism is writable.
    """
    with ui.kafkainteraction():
        try:
            partitions = ui.replicationpartitions
            for partition in partitions:
                ui.status(b"sending heartbeat to partition %d\n" % partition)
                vcsrproducer.send_heartbeat(ui.replicationproducer, partition=partition)
        except kafkacommon.KafkaError as e:
            ui.producerlog(
                "<unknown>", "EXCEPTION", "%s: %s" % (e, traceback.format_exc())
            )
            raise error.Abort(
                b"error sending heartbeat: %s" % pycompat.bytestr(str(e.message))
            )

    ui.status(_(b"wrote heartbeat message into %d partitions\n") % len(partitions))


@command(
    b"replicatesync",
    [
        (b"b", b"bootstrap", False, b"Use bootstrap mode"),
        (b"h", b"heads", True, b"Send heads message"),
    ],
    b"replicate this repository to mirrors",
)
def replicatecommand(ui, repo, **opts):
    """Tell mirrors to synchronize their copy of this repo.

    This is intended as a support command to be used to force replication.
    If the replication system is working as intended, it should not need to be
    used.
    """
    sendreposyncmessage(ui, repo, bootstrap=opts.get("bootstrap"))
    ui.status(_(b"wrote synchronization message into replication log\n"))

    if opts.get("heads") and not opts.get("bootstrap"):
        sendheadsmessage(ui, repo)
        ui.status(_(b"wrote heads synchronization message into replication log\n"))


@command(b"replicatedelete", [], b"delete this repository and all mirrors")
def replicatedelete(ui, repo):
    """Remove repo and synchronize deletion across mirrors.

    This is intended as a mechanism to perform a repo deletion with a single
    command, from the master hgssh host.
    """
    repo_dir = repo.root

    try:
        sendrepodeletemessage(ui, repo)
        ui.status(_(b"wrote delete message into replication log\n"))

        todelete_repo_name = repo.root + b".todelete"

        os.rename(repo.root, todelete_repo_name)
        shutil.rmtree(todelete_repo_name)
        ui.status(_(b"repo deleted from local host\n"))

    except IOError as e:
        raise error.Abort(_(b"could not delete repo %s: %s\n" % (repo_dir, e)))


@command(
    b"debugbase85obsmarkers",
    [(b"T", b"template", b"json", _(b"display with template"), _(b"TEMPLATE"))],
    b"MARKERS",
    norepo=True,
)
def debugbase85obsmarkers(ui, markers, **opts):
    """Print information about base85 obsolescence markers."""
    data = base85.b85decode(markers)
    version, markers = obsolete._readmarkers(data)

    with ui.formatter(b"debugbase85obsmarkers", pycompat.byteskwargs(opts)) as fm:
        for precursor, successors, flags, metadata, date, parents in markers:
            fm.startitem()

            if parents:
                parents = [hex(n) for n in parents]

            successors = [hex(n) for n in successors]

            fm.write(b"precursor", b"precursor: %s\n", hex(precursor))
            fm.write(
                b"successors",
                b"successors: %s\n",
                fm.formatlist(successors, b"successor"),
            )
            fm.write(b"flags", b"flags: %d\n", flags)
            fm.write(
                b"metadata", b"metadata: %s\n", fm.formatlist(metadata, b"metadata")
            )
            fm.write(b"date", b"date: %s\n", fm.formatdate(date))
            fm.condwrite(parents, b"parents", b"parents: %s\n", parents)


def wireprotodispatch(orig, repo, proto, command, **kwargs):
    """Wraps wireprotov1server.dispatch() to allow operations on unfiltered repo.

    Replication consumers need full access to the source repo. The
    default implementation of ``wireprotov1server.dispatch`` always operated on
    the ``served`` repo filter, which doesn't expose hidden changesets.
    This could cause replication mirrors referencing hidden changesets
    to encounter errors.

    If the current user is the configured user that can access unfiltered
    repo views, we operate on the unfiltered repo.
    """
    unfiltereduser = repo.ui.config(b"replication", b"unfiltereduser")
    if not unfiltereduser or unfiltereduser != repo.ui.environ.get(b"USER"):
        return orig(repo, proto, command, **kwargs)

    # We operate on the repo.unfiltered() instance because attempting
    # to adjust the class on a repoview class can result in infinite recursion.
    urepo = repo.unfiltered()
    origclass = urepo.__class__

    class unfilteroncerepo(origclass):
        def filtered(self, name, *args, **kwargs):
            unfiltered = self.unfiltered()
            unfiltered.__class__ = origclass
            return unfiltered

    try:
        urepo.__class__ = unfilteroncerepo
        return orig(repo, proto, command, **kwargs)
    finally:
        urepo.__class__ = origclass


def wrapped_getdispatchrepo(orig, repo, proto, command, **kwargs):
    """Wraps `wireprotov1server.getdispatchrepo` to serve the unfiltered repository"""
    unfiltereduser = repo.ui.config(b"replication", b"unfiltereduser")
    if not unfiltereduser or unfiltereduser != repo.ui.environ.get(b"USER"):
        return orig(repo, proto, command, **kwargs)

    permission = wireprotov1server.commands[command].permission
    if permission == b"pull":
        return repo.unfiltered()
    return orig(repo, proto, command, **kwargs)


def extsetup(ui):
    extensions.wrapfunction(wireprotov1server, "dispatch", wireprotodispatch)
    extensions.wrapcommand(commands.table, b"init", initcommand)
    extensions.wrapfunction(
        wireprotov1server, "getdispatchrepo", wrapped_getdispatchrepo
    )

    if _ORIG_PHASE_HEADS_HANDLER:
        bundle2.parthandlermapping[b"phase-heads"] = phase_heads_handler
        phase_heads_handler.params = _ORIG_PHASE_HEADS_HANDLER.params

    # Configure null handler for kafka.* loggers to prevent "No handlers could
    # be found" messages from creeping into output.
    kafkalogger = logging.getLogger("kafka")
    if not kafkalogger.handlers:
        kafkalogger.addHandler(logging.NullHandler())


def uisetup(ui):
    # We assume that if the extension is loaded that we want replication
    # support enabled. Validate required config options are present.
    hosts = ui.configlist(b"replicationproducer", b"hosts")
    if not hosts:
        raise error.Abort(b"replicationproducer.hosts config option not set")

    clientid = ui.config(b"replicationproducer", b"clientid")
    if not clientid:
        raise error.Abort(b"replicationproducer.clientid config option not set")

    timeout = ui.configint(b"replicationproducer", b"connecttimeout", 10)

    topic = ui.config(b"replicationproducer", b"topic")
    if not topic:
        raise error.Abort(b"replicationproducer.topic config option not set")

    def havepartitionmap():
        for k, v in ui.configitems(b"replicationproducer"):
            if k.startswith(b"partitionmap."):
                return True
        return False

    if not havepartitionmap():
        raise error.Abort(
            b"replicationproducer.partitionmap.* config options not set"
        )

    reqacks = ui.configint(b"replicationproducer", b"reqacks", default=999)
    if reqacks not in (-1, 0, 1):
        raise error.Abort(b"replicationproducer.reqacks must be set to -1, 0, or 1")

    acktimeout = ui.configint(b"replicationproducer", b"acktimeout")
    if not acktimeout:
        raise error.Abort(b"replicationproducer.acktimeout config option not set")

    # TRACKING py3
    hosts = list(map(lambda x: pycompat.sysstr(x), hosts))
    clientid = pycompat.sysstr(clientid)
    topic = pycompat.sysstr(topic)

    class replicatingui(ui.__class__):
        """Custom ui class that provides access to replication primitives."""

        @property
        def replicationproducer(self):
            """Obtain a ``Producer`` instance to write to the replication log."""
            if not getattr(self, "_replicationproducer", None):
                client = SimpleClient(hosts, client_id=clientid, timeout=timeout)
                self._replicationproducer = vcsrproducer.Producer(
                    client,
                    topic,
                    batch_send=False,
                    req_acks=reqacks,
                    ack_timeout=acktimeout,
                )

            return self._replicationproducer

        @property
        def replicationpartitionmap(self):
            pm = {}
            replicationproduceritems = (
                (
                    pycompat.sysstr(k),
                    pycompat.sysstr(v),
                )
                for k, v in self.configitems(b"replicationproducer")
            )
            for k, v in replicationproduceritems:
                # Ignore unrelated options in this section.
                if not k.startswith("partitionmap."):
                    continue

                parts, expr = v.split(":", 1)
                parts = [int(x.strip()) for x in parts.split(",")]
                pm[k[len("partitionmap.") :]] = (parts, re.compile(expr))

            if not pm:
                raise error.Abort(_(b"partitions not defined"))

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
                self.producerlog(
                    "<unknown>",
                    "KAFKA_EXCEPTION",
                    "%s: %s" % (e, traceback.format_exc()),
                )
                raise

        def producerlog(self, repo, action, *args):
            """Write to the producer syslog facility."""
            ident = self.config(
                b"replicationproducer", b"syslogident", b"vcsreplicator"
            )
            facility = self.config(
                b"replicationproducer", b"syslogfacility", b"LOG_LOCAL2"
            )

            if not ident or not facility:
                raise error.Abort(
                    b"syslog identity or facility missing from "
                    b"replicationproducer config"
                )

            ident = pycompat.sysstr(ident)
            facility = pycompat.sysstr(facility)

            facility = getattr(syslog, facility)
            syslog.openlog(ident, 0, facility)

            if not isinstance(repo, (bytes, str)):
                repo = repo.replicationwireprotopath

            pre = "%s %s %s" % (os.environ.get("USER", "<unknown>"), repo, action)
            syslog.syslog(syslog.LOG_NOTICE, "%s %s" % (pre, " ".join(args)))
            syslog.closelog()

    ui.__class__ = replicatingui


def reposetup(ui, repo):
    if not repo.local():
        return

    ui.setconfig(b"hooks", b"precommit.vcsreplicator", precommithook, b"vcsreplicator")
    ui.setconfig(
        b"hooks", b"pretxnopen.vcsreplicator", pretxnopenhook, b"vcsreplicator"
    )
    ui.setconfig(b"hooks", b"pushkey.vcsreplicator", pushkeyhook, b"vcsreplicator")
    ui.setconfig(
        b"hooks",
        b"pretxnchangegroup.vcsreplicator",
        pretxnchangegrouphook,
        b"vcsreplicator",
    )
    ui.setconfig(
        b"hooks", b"pretxnclose.vcsreplicator", pretxnclosehook, b"vcsreplicator"
    )
    ui.setconfig(b"hooks", b"txnclose.vcsreplicator", txnclosehook, b"vcsreplicator")
    ui.setconfig(
        b"hooks", b"changegroup.vcsreplicator", changegrouphook, b"vcsreplicator"
    )

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
            lower = pycompat.sysstr(self.root.lower())
            for source, dest in self.ui.configitems(b"replicationpathrewrites"):
                if lower.startswith(pycompat.sysstr(source)):
                    return pycompat.sysstr(dest) + pycompat.sysstr(
                        self.root[len(source) :]
                    )

            raise error.Abort(
                b"repository path not configured for replication",
                hint=b"add entry to [replicationpathrewrites]",
            )

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
                h.update(pycompat.bytestr(path))
                i = int(h.hexdigest(), 16)
                offset = i % len(parts)
                return parts[offset]

            raise error.Abort(
                _(b"unable to map repo to partition"),
                hint=_(b'define a partition map with a ".*" ' b"fallback"),
            )

        def producerlog(self, action, *args):
            return self.ui.producerlog(self, action, *args)

    repo.__class__ = replicatingrepo
