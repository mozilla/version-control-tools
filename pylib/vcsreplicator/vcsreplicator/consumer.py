# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import os

import hglib
from kafka.consumer import SimpleConsumer


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
            auto_commit=False)

        self.fetch_last_known_offsets(partitions)

    def get_message(self, timeout=0.1):
        """Obtain and decode a message.

        If a message is available, it returns a tuple of the original
        OffsetAndMessage and the decoded payload, as a Python type.
        If a message is not available, None is returned.
        """
        message = super(Consumer, self).get_message(timeout=timeout)
        if not message:
            return message

        d = message.message.value
        if not d.startswith('1\n'):
            raise ValueError('unrecognized message payload. this is bad')

        payload = json.loads(d[2:])
        return message, payload


def consume(config, consumer, timeout=0.1, onetime=False):
    """Read messages from a consumer and process them as they arrive."""
    while True:
        r = consumer.get_message(timeout=timeout)
        if r:
            process_message(config, r[1])
            consumer.commit()

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
    hgrc_path = os.path.join(path, '.hg', 'hgrc')

    if content is None:
        if os.path.exists(hgrc_path):
            logger.warn('deleted hgrc from %s' % path)
            os.unlink(hgrc_path)

        return


    with open(hgrc_path, 'w') as fh:
        fh.write(content)

    logger.warn('wrote hgrc: %s' % hgrc_path)


if __name__ == '__main__':
    import argparse
    import sys
    import yaml
    from .config import Config

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file to load')
    parser.add_argument('--dump', action='store_true',
                        help='Dump available messages and exit')
    parser.add_argument('--onetime', action='store_true',
                        help='Process a single message and exit')
    parser.add_argument('--start-from', type=int,
                        help='Start N records from the beginning')

    args = parser.parse_args()

    config = Config(filename=args.config)

    consumer = config.consumer

    if args.start_from:
        consumer.seek(args.start_from, 0)

    if args.dump:
        messages = []
        while True:
            m = consumer.get_message()
            if not m:
                break
            messages.append(m[1])

        print(yaml.safe_dump(messages, default_flow_style=False).rstrip())
        sys.exit(0)

    logging.basicConfig()
    consume(config, consumer, onetime=args.onetime)
