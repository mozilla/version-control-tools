# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import os
import sys
import time

import hglib
from kafka.consumer import SimpleConsumer

from .util import wait_for_topic

logger = logging.getLogger('vcsreplicator.consumer')


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
            max_buffer_size=104857600)

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
        if not d.startswith('1\n'):
            raise ValueError('unrecognized message payload. this is bad')

        payload = json.loads(d[2:])
        return partition, message, payload


def consume(config, consumer, timeout=0.1, onetime=False):
    """Read messages from a consumer and process them as they arrive."""
    while True:
        r = consumer.get_message(timeout=timeout)
        if r:
            partition, message, payload = r
            process_message(config, payload)
            # Only commit offset from partition message came from.
            consumer.commit(partitions=[partition])

        if onetime:
            break


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

    logger.warn('writing hgrc: %s' % p)
    with open(p, 'wb') as fh:
        fh.write(content)


if __name__ == '__main__':
    import argparse
    import sys
    import yaml
    from .config import Config

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
    consume(config, consumer, onetime=args.onetime)
