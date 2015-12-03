# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import os
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

logger = logging.getLogger('vcsreplicator.consumer')

MAX_BUFFER_SIZE = 104857600 # 100 MB

MESSAGE_HEADER_V1 = b'1\n'


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
            max_buffer_size=MAX_BUFFER_SIZE)

        self.fetch_last_known_offsets(partitions)

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
        if not d.startswith(MESSAGE_HEADER_V1):
            raise ValueError('unrecognized message payload. this is bad')

        payload = json.loads(d[2:])
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
    elif name == 'hg-hgrc-update-1':
        return process_hg_hgrc_update(config, payload['path'],
                                      payload['content'])
    elif name == 'hg-changegroup-1':
        return process_hg_changegroup(config, payload['path'],
                                      payload['source'],
                                      payload['nodes'],
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

    raise ValueError('unrecognized message type: %s' % payload['name'])


def process_hg_repo_init(config, path):
    """Process a Mercurial repository initialization message."""
    logger.debug('received request to create repo: %s' % path)

    path = config.parse_wire_repo_path(path)
    hgpath = os.path.join(path, '.hg')
    if os.path.exists(hgpath):
        logger.warn('repository already exists: %s' % path)
        return

    # We can't use hglib.init() because it doesn't pass config options
    # as part of the `hg init` call.
    args = hglib.util.cmdbuilder('init', path)
    args.insert(0, hglib.HGPATH)
    proc = hglib.util.popen(args)
    out, err = proc.communicate()
    if proc.returncode:
        raise Exception('error creating Mercurial repo %s: %s' % (path, out))

    logger.warn('created Mercurial repository: %s' % path)


def process_hg_hgrc_update(config, path, content):
    """Process a message indicating the hgrc is to be updated."""
    logger.debug('received hgrc update for repo: %s' % path)

    path = config.parse_wire_repo_path(path)
    update_hgrc(path, content)


def process_hg_changegroup(config, path, source, nodes, heads):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log('tip')[0].rev)

        logger.warn('pulling %d heads (%s) and %d nodes from %s into %s' % (
            len(heads), ', '.join(heads), len(nodes), url, local_path))

        c.pull(source=url or 'default', rev=heads)
        newtip = int(c.log('tip')[0].rev)

        if newtip - oldtip != len(nodes):
            logger.warn('mismatch between expected and actual changeset count: '
                        'expected %d, got %d' % (len(nodes), newtip - oldtip))

        logger.warn('pulled %d changesets into %s' % (newtip - oldtip,
                                                      local_path))


def process_hg_pushkey(config, path, namespace, key, old, new, ret):
    path = config.parse_wire_repo_path(path)
    with get_hg_client(path) as c:
        logger.info('executing pushkey on %s for %s[%s]' %
                    (path, namespace, key))
        c.rawcommand(['debugpushkey', path, namespace, key, old, new])
        logger.info('finished pushkey on %s for %s[%s]' %
                    (path, namespace, key))


def process_hg_sync(config, path, requirements, hgrc, heads):
    local_path = config.parse_wire_repo_path(path)
    url = config.get_pull_url_from_repo_path(path)

    # TODO create repo when missing.
    if not os.path.exists(local_path):
        logger.warn('repository does not exist: %s' % local_path)
        return

    # TODO set or warn about different requirements.

    update_hgrc(local_path, hgrc)

    with get_hg_client(local_path) as c:
        oldtip = int(c.log('tip')[0].rev)

        logger.warn('pulling %d heads into %s' % (
            len(heads), local_path))
        c.pull(source=url or 'default')

        newtip = int(c.log('tip')[0].rev)

        logger.warn('pulled %d changesets into %s' % (newtip - oldtip,
                                                      local_path))


def get_hg_client(path):
    return hglib.open(path, encoding='UTF-8',
                      configs=['vcsreplicator.disableproduce=true'])


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
                p, message, payload = consumer.get_message()
                lag_time = time.time() - payload['_created']
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

    args = parser.parse_args()

    config = Config(filename=args.config)
    client = config.get_client_from_section('consumer', timeout=30)
    topic = config.c.get('consumer', 'topic')
    group = config.c.get('consumer', 'group')
    wait_for_topic(client, topic, 30)

    partitions = None
    if args.partition is not None:
        partitions = [args.partition]

    consumer = Consumer(client, group, topic, partitions)

    if args.start_from:
        consumer.seek(args.start_from, 0)

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
    formatter = logging.Formatter(
            '%(asctime)s %(process)d %(name)s %(message)s',
            '%Y-%m-%dT%H:%M:%SZ')
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if not args.onetime:
        logger.warn('starting consumer for topic=%s group=%s partitions=%s' % (
            topic, group, partitions or 'all'))
    try:
        consume(config, consumer, onetime=args.onetime)
        if not args.onetime:
            logger.warn('process exiting gracefully')
    except BaseException:
        logger.error('exiting main consume loop with error')
        raise
