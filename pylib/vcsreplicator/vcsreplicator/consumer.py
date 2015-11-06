# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging

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

    raise ValueError('unrecognized message type: %s' % payload['name'])


def process_hg_repo_init(config, path):
    """Process a Mercurial repository initialization message."""
    print('TODO got a hg init message for %s' % path)


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

    args = parser.parse_args()

    config = Config(filename=args.config)

    consumer = config.consumer

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
