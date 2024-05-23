# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import binascii
import errno
import functools
import io
import json
import logging
import os
import pipes
import shutil
import signal
import sys
import time

import cbor2
import hglib
from kafka.consumer import SimpleConsumer

from mercurial import (
    pycompat,
)

from .config import Config
from .util import (
    consumer_offsets,
    payload_log_display,
    wait_for_topic,
)


HERE = os.path.abspath(os.path.dirname(__file__))
CONSUMER_EXT = os.path.join(HERE, "consumerext.py")


logger = logging.getLogger("vcsreplicator.consumer")

MIN_BUFFER_SIZE = 1048576  # 1 MB

MAX_BUFFER_SIZE = 104857600  # 100 MB

MESSAGE_HEADER_V1 = b"1\n"


def value_deserializer(value):
    """Deserializes vcsreplicator Kafka message values"""
    if not value.startswith(MESSAGE_HEADER_V1):
        raise ValueError("unrecognized message payload. this is bad")

    payload = json.loads(value[2:])
    return payload


class Consumer(SimpleConsumer):
    """A Kafka Consumer with sane defaults.

    We want auto commit disabled because we don't want to commit until
    after a message has been processed (not just read). SimpleConsumer/Consumer
    doesn't populate fetch offsets unless auto commit is enabled. We hack
    around that.
    """

    def __init__(self, client, group, topic, partitions):
        super(Consumer, self).__init__(
            client,
            group,
            topic,
            partitions=partitions,
            auto_commit=False,
            buffer_size=MIN_BUFFER_SIZE,
            max_buffer_size=MAX_BUFFER_SIZE,
        )

        self.fetch_last_known_offsets(partitions)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def get_message(self, timeout=0.1):
        """Obtain and decode a message.

        If a message is available, it returns a tuple of the partition,
        original ``OffsetAndMessage`` and the decoded payload, as a Python
        type. If a message is not available, ``None`` is returned.
        """
        res = super(Consumer, self).get_message(
            timeout=timeout, get_partition_info=True
        )
        if res is None:
            return None

        partition, message = res

        d = message.message.value
        payload = value_deserializer(d)

        return partition, message, payload


def consume(config, consumer, message_handler, timeout=0.1, onetime=False):
    """Read messages from a consumer and process them as they arrive.

    This loop runs forever until asked to exit via a SIGINT or SIGTERM.

    ``message_handler`` is a callable that will receive the ``(config,
    payload)`` of the message to process.
    """
    count = [0]

    class ShutDownException(Exception):
        pass

    def signal_exit(signum, frame):
        logger.warn("received signal %d" % signum)
        raise ShutDownException()

    oldint = signal.signal(signal.SIGINT, signal_exit)
    oldterm = signal.signal(signal.SIGTERM, signal_exit)

    try:
        while True:
            r = consumer.get_message(timeout=timeout)
            if r:
                partition, message, payload = r
                logger.warn(
                    "processing %s from partition %s offset %s"
                    % (payload_log_display(payload), partition, message.offset)
                )
                message_handler(config, payload)
                # Only commit offset from partition message came from.
                consumer.commit(partitions=[partition])
            if onetime:
                break
    except ShutDownException:
        logger.warn("exiting from main consume loop")
    finally:
        signal.signal(signal.SIGINT, oldint)
        signal.signal(signal.SIGTERM, oldterm)


def repofilter(message_handler):
    """Decorator for wrap message handler functions to ignore
    messages from filtered repositories.
    """

    @functools.wraps(message_handler)
    def filterwrapper(config, payload):
        repo = payload.get("path")

        # No repo in payload, heartbeat message
        if not repo:
            return

        res = config.filter(repo)

        if not res.passes_filter:
            logger.warn("repo %s filtered by rule %s" % (repo, res.rule))
            return

        return message_handler(config, payload)

    return filterwrapper


def autorecover(message_handler):
    """Automatically run `hg recover` when suggested in the output of
    the failed `hg` command.
    """

    @functools.wraps(message_handler)
    def autorecoverwrapper(config, payload):
        try:
            return message_handler(config, payload)
        except hglib.error.CommandError as err:
            # Attempt to recover a dead transaction without human interaction
            if b"run 'hg recover' to clean up transaction" not in err.err:
                raise err

            logger.warn("attempting to autorecover from abandoned transaction")

            path = config.parse_wire_repo_path(payload["path"])
            with get_hg_client(path) as c:
                args = hglib.util.cmdbuilder("recover")
                res, out, err = run_command(c, args)
                if res:
                    logger.warn(
                        "`hg recover` failed to automatically resolve the problem"
                    )
                    raise err

            return message_handler(config, payload)

    return autorecoverwrapper


@repofilter
@autorecover
def handle_message_main(config, payload):
    """Process a decoded event message.

    This represents message processing for the main consumer process. It
    is responsible for applying most messages.
    """

    name = payload["name"]
    if name == "heartbeat-1":
        return
    elif name == "hg-repo-init-1":
        return process_hg_repo_init(config, payload["path"])
    elif name == "hg-repo-init-2":
        return process_hg_repo_init(
            config, payload["path"], generaldelta=payload["generaldelta"]
        )
    elif name == "hg-hgrc-update-1":
        return process_hg_hgrc_update(config, payload["path"], payload["content"])
    elif name == "hg-changegroup-1":
        return process_hg_changegroup(
            config,
            payload["path"],
            payload["source"],
            len(payload["nodes"]),
            payload["heads"],
        )
    elif name == "hg-changegroup-2":
        return process_hg_changegroup(
            config,
            payload["path"],
            payload["source"],
            payload["nodecount"],
            payload["heads"],
        )
    elif name == "hg-pushkey-1":
        return process_hg_pushkey(
            config,
            payload["path"],
            payload["namespace"],
            payload["key"],
            payload["old"],
            payload["new"],
            payload["ret"],
        )
    elif name == "hg-repo-sync-1":
        return process_hg_sync(
            config,
            payload["path"],
            payload["requirements"],
            payload["hgrc"],
            payload["heads"],
        )
    elif name == "hg-repo-sync-2":
        # If the bootstrap field is set, this message should not
        # be consumed by the caller of this function (ie the
        # vcsreplicator consumer processes)
        if payload["bootstrap"]:
            return

        return process_hg_sync(
            config,
            payload["path"],
            payload["requirements"],
            payload["hgrc"],
            payload["heads"],
        )
    elif name == "hg-heads-1":
        # This message is handled by the heads consumer.
        return
    elif name == "hg-repo-delete-1":
        return process_hg_delete(config, payload["path"])

    raise ValueError("unrecognized message type: %s" % payload["name"])


@repofilter
def handle_message_heads(config, payload):
    """Process a decoded event message.

    This handles message processing for the heads consumer process.
    """
    name = payload["name"]
    if name == "hg-heads-1":
        return process_hg_heads(
            config, payload["path"], payload["heads"], payload["last_push_id"]
        )

    # All other messages are no-ops. We allow all unknown message types
    # through.


def init_repo(path):
    """Initializes a new hg repo at the specified path"""
    # We can't use hglib.init() because it doesn't pass config options
    # as part of the `hg init` call.
    args = hglib.util.cmdbuilder("init", path)
    args.insert(0, hglib.HGPATH)

    proc = hglib.util.popen(args)
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError(args, proc.returncode, out, err)

    logger.warn("created Mercurial repository: %s" % path)


def process_hg_repo_init(config, path, generaldelta=False):
    """Process a Mercurial repository initialization message."""
    logger.debug("received request to create repo: %s" % path)

    path = config.parse_wire_repo_path(path)
    hgpath = os.path.join(path, ".hg")
    if os.path.exists(hgpath):
        logger.warn("repository already exists: %s" % path)
        return

    init_repo(path)


def process_hg_hgrc_update(config, path, content):
    """Process a message indicating the hgrc is to be updated."""
    logger.debug("received hgrc update for repo: %s" % path)

    path = config.parse_wire_repo_path(path)
    update_hgrc(path, content)


def process_hg_changegroup(config, path, source, node_count, heads):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log("tip")[0].rev)

        logger.warn(
            "pulling %d heads (%s) and %d nodes from %s into %s"
            % (len(heads), ", ".join(heads), node_count, url, local_path)
        )

        args = hglib.util.cmdbuilder("pull", url or "default", r=heads)
        res, out, err = run_command(c, args)
        if res:
            raise hglib.error.CommandError(args, res, out, err)

        newtip = int(c.log("tip")[0].rev)

        # This logic isn't always accurate. For example, if the real tip is
        # hidden, 'tip' could be N-1. If a single changeset is pushed, it will
        # have value N+1. 2 != 1 will trigger this warning incorrectly.
        if newtip - oldtip != node_count:
            logger.warn(
                "mismatch between expected and actual changeset count: "
                "expected %d, got %d" % (node_count, newtip - oldtip)
            )

        logger.warn("pulled %d changesets into %s" % (newtip - oldtip, local_path))


def process_hg_pushkey(config, path, namespace, key, old, new, ret):
    path = config.parse_wire_repo_path(path)
    with get_hg_client(path) as c:
        logger.warn("executing pushkey on %s for %s[%s]" % (path, namespace, key))

        args = ["debugpushkey", path, namespace, key, old, new]
        res, out, err = run_command(c, args)

        if res and res != ret:
            raise hglib.error.CommandError(args, res, out, err)


def stream_clone_repo(canonical_path, local_path):
    """Stream clone the canonical repo to the local path.
    Returns on success and raises on error.
    """
    args = hglib.util.cmdbuilder(
        "clone", canonical_path, local_path, stream=True, noupdate=True
    )
    args.insert(0, hglib.HGPATH)
    logger.warn("performing stream clone of %s to %s" % (canonical_path, local_path))

    proc = hglib.util.popen(args)
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError(args, proc.returncode, out, err)

    logger.warn("%s cloned to %s successfully" % (canonical_path, local_path))


def process_hg_sync(config, path, requirements, hgrc, heads, create=False):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    if not os.path.exists(local_path):
        logger.warn("repository does not exist: %s" % local_path)
        if not create:
            return

        # Attempt to stream clone the repo from a clonebundle to maximize performance,
        # then follow up with a regular `hg pull` to ensure repo metadata
        # is replicated. This will fail if a clonebundle is not available
        # for download due to permissions on the master server (ie in tests)
        # so we fall back to the pull protocol.
        try:
            stream_clone_repo(url, local_path)
        except hglib.error.CommandError as e:
            logger.warn("stream clone of %s failed - using pull instead" % url)
            init_repo(local_path)

    # TODO set or warn about different requirements.

    update_hgrc(local_path, hgrc)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log("tip")[0].rev)

        logger.warn("pulling %d heads into %s" % (len(heads), local_path))
        args = hglib.util.cmdbuilder("pull", url or "default", r=heads)
        res, out, err = run_command(c, args)
        if res not in (0, 1):
            raise hglib.error.CommandError(args, res, out, err)

        newtip = int(c.log("tip")[0].rev)

        logger.warn("pulled %d changesets into %s" % (newtip - oldtip, local_path))


def process_hg_delete(config, wire_path):
    """Process message indicating repository at path should be deleted"""
    local_path = config.parse_wire_repo_path(wire_path)

    # Don't delete repos on backup nodes
    if config.is_backup():
        logger.warn("node is a backup; ignoring delete for %s" % local_path)
        return

    if not os.path.exists(local_path):
        logger.warn(
            "delete message received for path that does not exist: %s" % local_path
        )
        return

    # Use configured `todelete_path` if available
    if config.c.has_section("consumer") and config.c.has_option(
        "consumer", "todelete_path"
    ):
        todelete_path = config.get("consumer", "todelete_path")
    else:
        todelete_path = "/repo/hg/todelete"

    try:
        logger.info("deleting repo at %s" % local_path)

        destination = wire_path.replace("{moz}", todelete_path)
        logger.info("moving %s to %s" % (local_path, destination))

        try:
            os.makedirs(os.path.dirname(destination))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        os.rename(local_path, destination)

        logger.info("deleting repo at %s" % destination)
        shutil.rmtree(destination)
    except OSError as e:
        logger.warn("could not delete repo at %s: %s" % (local_path, e))
    logger.warn("repository at %s deleted" % local_path)


def process_hg_heads(config, path, heads, last_push_id):
    local_path = config.parse_wire_repo_path(path)

    logger.warn("updating replicated data for %s" % local_path)

    # We atomically write out a machine-readable file containing heads at
    # <repo>/.hg/replicated-heads. It is important that readers *always* have
    # a consistent snapshot of this file. Hence the use of a temporary file
    # and atomic rename.
    dest = os.path.join(local_path, ".hg", "replicated-data")
    dest_tmp = "%s.tmp" % dest

    if any(len(h) != 40 for h in heads):
        raise ValueError("expected 40 byte hex heads in message")

    with open(dest_tmp, "wb") as fh:
        data = {
            # May be None or an integer.
            b"last_push_id": last_push_id,
            # Heads are in hex. We store in binary for reading efficiency.
            b"heads": list(map(binascii.unhexlify, heads)),
        }

        cbor2.dump(data, fh, canonical=True)

    # If we're replacing a file, we need to ensure the mtime is advanced,
    # otherwise things caching the file may not see multiple updates in rapid
    # succession and may hold onto an earlier update. We can't just "touch"
    # the file because filesystem mtime resolution may not be that fine
    # grained. So we ensure the mtime is always incremented by at least 2s.
    try:
        st = os.stat(dest)
        old_mtime = st.st_mtime
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

        old_mtime = 0

    new_mtime = os.stat(dest_tmp).st_mtime
    if new_mtime <= old_mtime + 2:
        os.utime(dest, (old_mtime + 2, old_mtime + 2))
        logger.warn(
            "advanced mtime of %s from %d to %d" % (dest, old_mtime, old_mtime + 2)
        )

    os.rename(dest_tmp, dest)
    logger.warn(
        "%s wrote with %d heads successfully; last push id: %d"
        % (dest, len(heads), last_push_id)
    )


def get_hg_client(path):
    configs = [
        # This engages some client-specific functionality to mirror changes
        # instead of using default Mercurial semantics.
        "extensions.vcsreplicatorconsumer=%s" % CONSUMER_EXT,
        # Disable aggressive merge deltas, which some repos may have in their
        # .hg/hgrc. Aggressive merge deltas will force the consumer to
        # recompute deltas on merges against both parents. This will
        # significantly slow down replication. The deltas on the canonical
        # server should have already had this logic applied. And it is
        # redundant to do it on the consumers.
        "format.aggressivemergedeltas=false",
    ]

    return hglib.open(path, encoding="UTF-8", configs=configs)


def run_command(client, args):
    """Run a Mercurial command through a client.

    This is kind of like ``client.rawcommand()`` except it performs logging
    and doesn't do fancy error handling.
    """
    combined = io.BytesIO()
    out = io.BytesIO()
    err = io.BytesIO()

    def log_combined():
        v = combined.getvalue()

        if not v or b"\n" not in v:
            return

        lines = v.splitlines()
        for line in lines:
            logger.warn("  > %s" % pycompat.sysstr(line))

        # Truncate the stream.
        combined.seek(0)
        combined.truncate()

        # Restore the final line fragment if there is one.
        if not v.endswith(b"\n"):
            combined.write(lines[-1])

    def write_out(s):
        out.write(s)
        combined.write(s)
        log_combined()

    def write_err(s):
        err.write(s)
        combined.write(s)
        log_combined()

    channels = {
        b"o": write_out,
        b"e": write_err,
    }

    quoteable_args = [pycompat.sysstr(arg) for arg in [hglib.HGPATH] + args]

    logger.warn("  $ %s" % " ".join(map(pipes.quote, quoteable_args)))

    unquotable_args = [pycompat.bytestr(arg) for arg in quoteable_args]

    ret = client.runcommand(unquotable_args[1:], {}, channels)
    logger.warn("  [%d]" % ret)

    return ret, out.getvalue(), err.getvalue()


def update_hgrc(repo_path, content):
    """Update the .hg/hgrc file for a repo with content.

    If ``content`` is None, the file will be removed.
    """
    p = os.path.join(repo_path, ".hg", "hgrc")
    if content is None:
        if os.path.exists(p):
            logger.warn("deleting hgrc from %s" % repo_path)
            os.unlink(p)

        return

    assert isinstance(content, pycompat.unicode)
    logger.warn("writing hgrc: %s" % p)
    with open(p, "wb") as fh:
        fh.write(content.encode("utf-8"))


def consumer_offsets_and_lag(client, topic, groups):
    """Obtain consumer fetch offsets and lag.

    Returns a dict mapping group name to dict of partition to consumer
    information. The consumer information is a tuple of:

        (current_offset, available_offset, lag_time)

    ``lag_time`` will be 0.0 if the consumer is fully caught up.
    """
    offsets = consumer_offsets(client, topic, groups)
    res = {}

    # Replace the consume offset with offset + time lag.
    for group in offsets["group"]:
        res[group] = {}
        for partition, offset in sorted(offsets["group"][group].items()):
            available = offsets["available"][partition]
            lag = available - offset
            if lag > 0:
                consumer = Consumer(client, group, topic, partitions=[partition])
                consumer.seek(offset, 0)
                # We may not always be able to fetch a message, surprisingly.
                # Use a higher timeout to try harder.
                # NRPE requires a response within 10s or it complains. So keep
                # the timeout low.
                raw_message = consumer.get_message(timeout=2.0)
                if raw_message:
                    p, message, payload = raw_message
                    lag_time = time.time() - payload["_created"]
                else:
                    # If we failed to get a message, something is wrong. Store
                    # None as a special value.
                    lag_time = None
            else:
                lag_time = 0.0

            res[group][partition] = (offset, available, lag_time)

    return res


def print_offsets():
    """CLI command to print current consumer offsets and lag.

    Receives as arguments the path to a config file and list of consumer
    groups to print info for.
    """
    import argparse
    import tabulate

    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config file to load")
    parser.add_argument(
        "group",
        nargs="?",
        help="Comma delimited list of consumer groups to print offsets for",
    )

    args = parser.parse_args()

    config = Config(filename=args.config)
    client = config.get_client_from_section("consumer", timeout=5)
    topic = config.get("consumer", "topic")

    if args.group:
        groups = [s.strip() for s in args.group.split(",")]
    else:
        groups = [config.get("consumer", "group")]

    d = consumer_offsets_and_lag(client, topic, groups)

    headers = (
        "topic",
        "group",
        "partition",
        "offset",
        "available",
        "lag (s)",
    )

    data = []
    for group in groups:
        for partition, (offset, available, lag_time) in sorted(d[group].items()):
            if lag_time is None:
                lag_time = "error"
            data.append((topic, group, partition, offset, available, lag_time))

    print(tabulate.tabulate(data, headers))
    sys.exit(0)


def run_cli(message_handler):
    """Command line interface to consumer.

    ``message_handler`` is the message processing callable to be used when
    messages are acted upon.
    """
    import argparse
    import yaml

    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)

    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config file to load")
    parser.add_argument(
        "--dump", action="store_true", help="Dump available messages and exit"
    )
    parser.add_argument(
        "--onetime", action="store_true", help="Process a single message and exit"
    )
    parser.add_argument(
        "--start-from", type=int, help="Start N records from the beginning"
    )
    parser.add_argument(
        "--partition",
        type=int,
        help="Partition to fetch from. Defaults to all partitions.",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Skip the consuming of the next message then exit",
    )
    parser.add_argument(
        "--wait-for-no-lag",
        action="store_true",
        help="Wait for consumer lag to be 0 messages and exit",
    )
    parser.add_argument(
        "--wait-for-n",
        type=int,
        help="Wait for N messages to become available then exit",
    )

    args = parser.parse_args()

    config = Config(filename=args.config)

    # hglib will use 'hg' which relies on PATH being correct. Since we're
    # running from a virtualenv, PATH may not be set unless the virtualenv
    # is activated. Overwrite the hglib defaults with a value from the config.
    hglib.HGPATH = config.hg_path

    client = config.get_client_from_section("consumer", timeout=30)
    topic = config.get("consumer", "topic")
    group = config.get("consumer", "group")
    poll_timeout = config.c.getfloat("consumer", "poll_timeout")
    wait_for_topic(client, topic, 30)

    if args.wait_for_no_lag:
        while True:
            d = consumer_offsets_and_lag(client, topic, [group])
            partitions = d[group]
            lagging = False
            for partition, (offset, available, lag_time) in partitions.items():
                lag = available - offset
                if lag > 0:
                    lagging = True

            if lagging:
                time.sleep(0.1)
            else:
                sys.exit(0)

    partitions = None
    if args.partition is not None:
        partitions = [args.partition]

    consumer = Consumer(client, group, topic, partitions)

    if args.start_from:
        consumer.seek(args.start_from, 0)

    if args.wait_for_n:
        left = args.wait_for_n
        while left > 0:
            m = consumer.get_message()
            if not m:
                continue

            print("got a %s message" % payload_log_display(m[2]))

            left -= 1

        sys.exit(0)

    if args.dump:
        messages = []
        while True:
            m = consumer.get_message()
            if not m:
                break
            messages.append(m[2])

        print(yaml.safe_dump(messages, default_flow_style=False).rstrip())
        sys.exit(0)

    if args.skip:
        r = consumer.get_message()
        if not r:
            print("no message available; nothing to skip")
            sys.exit(1)

        partition, message, payload = r
        consumer.commit(partitions=[partition])
        print("skipped message in partition %d for group %s" % (partition, group))
        sys.exit(0)

    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(name)s %(message)s")
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if not args.onetime:
        logger.warn(
            "starting consumer for topic=%s group=%s partitions=%s"
            % (topic, group, partitions or "all")
        )
    try:
        consume(
            config,
            consumer,
            message_handler,
            onetime=args.onetime,
            timeout=poll_timeout,
        )
        if not args.onetime:
            logger.warn("process exiting gracefully")
    except BaseException:
        logger.error("exiting main consume loop with error")
        raise


def consumer_cli():
    """Entrypoint for vcsreplicator-consumer executable."""
    run_cli(handle_message_main)


def heads_consumer_cli():
    """Entrypoint for vcsreplicator-headsconsumer executable."""
    run_cli(handle_message_heads)
