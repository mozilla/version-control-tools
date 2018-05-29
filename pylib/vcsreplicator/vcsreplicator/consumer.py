# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import io
import json
import logging
import os
import pipes
import signal
import sys
import time

import hglib
from kafka.consumer import SimpleConsumer

from .config import Config
from .util import (
    consumer_offsets,
    wait_for_topic,
)


HERE = os.path.abspath(os.path.dirname(__file__))
CONSUMER_EXT = os.path.join(HERE, 'consumerext.py')


logger = logging.getLogger('vcsreplicator.consumer')

MIN_BUFFER_SIZE = 1048576  # 1 MB

MAX_BUFFER_SIZE = 104857600 # 100 MB

MESSAGE_HEADER_V1 = b'1\n'


def value_deserializer(value):
    '''Deserializes vcsreplicator Kafka message values'''
    if not value.startswith(MESSAGE_HEADER_V1):
        raise ValueError('unrecognized message payload. this is bad')

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
            client, group, topic, partitions=partitions,
            auto_commit=False,
            buffer_size=MIN_BUFFER_SIZE,
            max_buffer_size=MAX_BUFFER_SIZE)

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
        res = super(Consumer, self).get_message(timeout=timeout,
                                                get_partition_info=True)
        if res is None:
            return None

        partition, message = res

        d = message.message.value
        payload = value_deserializer(d)

        return partition, message, payload


def consume(config, consumer, timeout=0.1, onetime=False):
    """Read messages from a consumer and process them as they arrive.

    This loop runs forever until asked to exit via a SIGINT or SIGTERM.
    """
    count = [0]

    def signal_exit(signum, frame):
        logger.warn('received signal %d' % signum)
        count[0] += 1

        if count[0] == 1:
            logger.warn('exiting gracefully')
            return

        # If this is a subsequent signal, convert to forceful exit.
        logger.warn('already received exit signal; forcefully aborting')
        sys.exit(1)

    oldint = signal.signal(signal.SIGINT, signal_exit)
    oldterm = signal.signal(signal.SIGTERM, signal_exit)

    try:
        while not count[0]:
            r = consumer.get_message(timeout=timeout)
            if r:
                partition, message, payload = r
                logger.warn('processing %s from partition %s offset %s' % (
                            payload['name'], partition, message.offset))
                process_message(config, payload)
                # Only commit offset from partition message came from.
                consumer.commit(partitions=[partition])

            if onetime:
                break

        if not onetime:
            logger.warn('exiting from main consume loop')
    finally:
        signal.signal(signal.SIGINT, oldint)
        signal.signal(signal.SIGTERM, oldterm)


def process_message(config, payload):
    """Process a decoded event message."""

    name = payload['name']
    if name == 'heartbeat-1':
        return
    elif name == 'hg-repo-init-1':
        return process_hg_repo_init(config, payload['path'])
    elif name == 'hg-repo-init-2':
        return process_hg_repo_init(config, payload['path'],
                                    generaldelta=payload['generaldelta'])
    elif name == 'hg-hgrc-update-1':
        return process_hg_hgrc_update(config, payload['path'],
                                      payload['content'])
    elif name == 'hg-changegroup-1':
        return process_hg_changegroup(config, payload['path'],
                                      payload['source'],
                                      len(payload['nodes']),
                                      payload['heads'])
    elif name == 'hg-changegroup-2':
        return process_hg_changegroup(config, payload['path'],
                                      payload['source'],
                                      payload['nodecount'],
                                      payload['heads'])
    elif name == 'hg-pushkey-1':
        return process_hg_pushkey(config, payload['path'],
                                  payload['namespace'],
                                  payload['key'],
                                  payload['old'],
                                  payload['new'],
                                  payload['ret'])
    elif name == 'hg-repo-sync-1':
        return process_hg_sync(config, payload['path'],
                               payload['requirements'],
                               payload['hgrc'],
                               payload['heads'])
    elif name == 'hg-repo-sync-2':
        # If the bootstrap field is set, this message should not
        # be consumed by the caller of this function (ie the
        # vcsreplicator consumer processes)
        if payload['bootstrap']:
            return

        return process_hg_sync(config, payload['path'],
                               payload['requirements'],
                               payload['hgrc'],
                               payload['heads'])

    raise ValueError('unrecognized message type: %s' % payload['name'])


def init_repo(path):
    '''Initializes a new hg repo at the specified path'''
    # We can't use hglib.init() because it doesn't pass config options
    # as part of the `hg init` call.
    args = hglib.util.cmdbuilder('init', path)
    args.insert(0, hglib.HGPATH)

    proc = hglib.util.popen(args)
    out, err = proc.communicate()
    if proc.returncode:
        raise Exception('error creating Mercurial repo %s: %s' % (path, out))

    logger.warn('created Mercurial repository: %s' % path)


def process_hg_repo_init(config, path, generaldelta=False):
    """Process a Mercurial repository initialization message."""
    logger.debug('received request to create repo: %s' % path)

    path = config.parse_wire_repo_path(path)
    hgpath = os.path.join(path, '.hg')
    if os.path.exists(hgpath):
        logger.warn('repository already exists: %s' % path)
        return

    init_repo(path)


def process_hg_hgrc_update(config, path, content):
    """Process a message indicating the hgrc is to be updated."""
    logger.debug('received hgrc update for repo: %s' % path)

    path = config.parse_wire_repo_path(path)
    update_hgrc(path, content)


def process_hg_changegroup(config, path, source, node_count, heads):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log('tip')[0].rev)

        logger.warn('pulling %d heads (%s) and %d nodes from %s into %s' % (
            len(heads), ', '.join(heads), node_count, url, local_path))

        args = hglib.util.cmdbuilder('pull', url or 'default', r=heads)
        res, out, err = run_command(c, args)
        if res:
            raise Exception('unexpected exit code during pull: %d' % res)

        newtip = int(c.log('tip')[0].rev)

        # This logic isn't always accurate. For example, if the real tip is
        # hidden, 'tip' could be N-1. If a single changeset is pushed, it will
        # have value N+1. 2 != 1 will trigger this warning incorrectly.
        if newtip - oldtip != node_count:
            logger.warn('mismatch between expected and actual changeset count: '
                        'expected %d, got %d' % (node_count, newtip - oldtip))

        logger.warn('pulled %d changesets into %s' % (newtip - oldtip,
                                                      local_path))


def process_hg_pushkey(config, path, namespace, key, old, new, ret):
    path = config.parse_wire_repo_path(path)
    with get_hg_client(path) as c:
        logger.warn('executing pushkey on %s for %s[%s]' %
                    (path, namespace, key))

        res, out, err = run_command(c, ['debugpushkey', path, namespace,
                                        key, old, new])

        if res and res != ret:
            raise Exception('unexpected exit code from pushkey on %s for '
                            '%s[%s]: %s' % (path, namespace, key, res))


def process_hg_sync(config, path, requirements, hgrc, heads, create=False):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    if not os.path.exists(local_path):
        logger.warn('repository does not exist: %s' % local_path)
        if not create:
            return

        init_repo(local_path)

    # TODO set or warn about different requirements.

    update_hgrc(local_path, hgrc)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log('tip')[0].rev)

        logger.warn('pulling %d heads into %s' % (
            len(heads), local_path))
        args = hglib.util.cmdbuilder('pull', url or 'default', r=heads)
        res, out, err = run_command(c, args)
        if res not in (0, 1):
            raise Exception('unexpected exit code from pull: %d' % res)

        newtip = int(c.log('tip')[0].rev)

        logger.warn('pulled %d changesets into %s' % (newtip - oldtip,
                                                      local_path))


def get_hg_client(path):
    # This engages some client-specific functionality to mirror changes instead
    # of using default Mercurial semantics.
    configs = ['extensions.vcsreplicatorconsumer=%s' % CONSUMER_EXT]

    return hglib.open(path, encoding='UTF-8', configs=configs)


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

        if not v or b'\n' not in v:
            return

        lines = v.splitlines()
        for line in lines:
            logger.warn(b'  > %s' % line)

        # Truncate the stream.
        combined.seek(0)
        combined.truncate()

        # Restore the final line fragment if there is one.
        if not v.endswith(b'\n'):
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
        b'o': write_out,
        b'e': write_err,
    }

    logger.warn('  $ %s' % ' '.join(
        map(pipes.quote, [hglib.HGPATH] + args)))
    ret = client.runcommand(args, {}, channels)
    logger.warn('  [%d]' % ret)

    return ret, out.getvalue(), err.getvalue()


def update_hgrc(repo_path, content):
    """Update the .hg/hgrc file for a repo with content.

    If ``content`` is None, the file will be removed.
    """
    p = os.path.join(repo_path, '.hg', 'hgrc')
    if content is None:
        if os.path.exists(p):
            logger.warn('deleting hgrc from %s' % repo_path)
            os.unlink(p)

        return

    assert isinstance(content, unicode)
    logger.warn('writing hgrc: %s' % p)
    with open(p, 'wb') as fh:
        fh.write(content.encode('utf-8'))


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
    for group in offsets['group']:
        res[group] = {}
        for partition, offset in sorted(offsets['group'][group].items()):
            available = offsets['available'][partition]
            lag = available - offset
            if lag > 0:
                consumer = Consumer(client, group, topic,
                                    partitions=[partition])
                consumer.seek(offset, 0)
                # We may not always be able to fetch a message, surprisingly.
                # Use a higher timeout to try harder.
                # NRPE requires a response within 10s or it complains. So keep
                # the timeout low.
                raw_message = consumer.get_message(timeout=2.0)
                if raw_message:
                    p, message, payload = raw_message
                    lag_time = time.time() - payload['_created']
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
    parser.add_argument('config',
            help='Path to config file to load')
    parser.add_argument('group', nargs='?',
            help='Comma delimited list of consumer groups to print offsets '
                 'for')

    args = parser.parse_args()

    config = Config(filename=args.config)
    client = config.get_client_from_section('consumer', timeout=5)
    topic = config.c.get('consumer', 'topic')

    if args.group:
        groups = [s.strip() for s in args.group.split(',')]
    else:
        groups = [config.c.get('consumer', 'group')]

    d = consumer_offsets_and_lag(client, topic, groups)

    headers = (
        'topic',
        'group',
        'partition',
        'offset',
        'available',
        'lag (s)',
    )

    data = []
    for group in groups:
        for partition, (offset, available, lag_time) in sorted(d[group].items()):
            if lag_time is None:
                lag_time = 'error'
            data.append((topic, group, partition, offset, available, lag_time))

    print(tabulate.tabulate(data, headers))
    sys.exit(0)


def cli():
    """Command line interface to consumer.

    This does a couple of things. We can probably split it up into separate
    functions.
    """
    import argparse
    import yaml

    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    parser = argparse.ArgumentParser()
    parser.add_argument('config',
            help='Path to config file to load')
    parser.add_argument('--dump', action='store_true',
            help='Dump available messages and exit')
    parser.add_argument('--onetime', action='store_true',
            help='Process a single message and exit')
    parser.add_argument('--start-from', type=int,
            help='Start N records from the beginning')
    parser.add_argument('--partition', type=int,
            help='Partition to fetch from. Defaults to all partitions.')
    parser.add_argument('--skip', action='store_true',
            help='Skip the consuming of the next message then exit')
    parser.add_argument('--wait-for-no-lag', action='store_true',
            help='Wait for consumer lag to be 0 messages and exit')
    parser.add_argument('--wait-for-n', type=int,
            help='Wait for N messages to become available then exit')

    args = parser.parse_args()

    config = Config(filename=args.config)

    # hglib will use 'hg' which relies on PATH being correct. Since we're
    # running from a virtualenv, PATH may not be set unless the virtualenv
    # is activated. Overwrite the hglib defaults with a value from the config.
    hglib.HGPATH = config.hg_path

    client = config.get_client_from_section('consumer', timeout=30)
    topic = config.c.get('consumer', 'topic')
    group = config.c.get('consumer', 'group')
    poll_timeout = config.c.getfloat('consumer', 'poll_timeout')
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

            name = m[2]['name']
            print('got a %s message' % name)

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
            print('no message available; nothing to skip')
            sys.exit(1)

        partition, message, payload = r
        consumer.commit(partitions=[partition])
        print('skipped message in partition %d for group %s' % (
            partition, group))
        sys.exit(0)

    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)s %(message)s')
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if not args.onetime:
        logger.warn('starting consumer for topic=%s group=%s partitions=%s' % (
            topic, group, partitions or 'all'))
    try:
        consume(config, consumer, onetime=args.onetime,
                timeout=poll_timeout)
        if not args.onetime:
            logger.warn('process exiting gracefully')
    except BaseException:
        logger.error('exiting main consume loop with error')
        raise
