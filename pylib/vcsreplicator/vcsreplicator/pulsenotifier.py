# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging
import sys

import kombu

from .config import (
    Config,
)
from .consumer import (
    Consumer,
)
from .daemon import (
    run_in_loop,
)
from .pushnotifications import (
    consume_one,
)


logger = logging.getLogger('vcsreplicator.pulsenotifier')


def on_push(config, repo_url, heads, source, pushlog_pushes):
    """Called when a push notification should be handled."""
    logger.warn('sending pulse notification for %s' % repo_url)

    c = config.c

    hostname = c.get('pulse', 'hostname')
    port = c.getint('pulse', 'port')
    userid = c.get('pulse', 'userid')

    logger.warn('connecting to pulse at %s:%d as %s' % (hostname, port, userid))

    conn = kombu.Connection(hostname=hostname,
                            port=port,
                            userid=userid,
                            password=c.get('pulse', 'password'),
                            virtual_host=c.get('pulse', 'virtual_host'),
                            ssl=c.getboolean('pulse', 'ssl'),
                            connect_timeout=c.getint('pulse', 'connect_timeout'))
    conn.connect()
    with conn:
        exchange = kombu.Exchange(c.get('pulse', 'exchange'), type='topic')
        producer = conn.Producer(exchange=exchange,
                                 routing_key=c.get('pulse', 'routing_key'),
                                 serializer='json')

        payload = {
            'payload': {
                'repo_url': repo_url,
                'heads': heads,
                'pushlog_pushes': pushlog_pushes,
            },
            '_meta': {
                'exchange': c.get('pulse', 'exchange'),
                'routing_key': c.get('pulse', 'routing_key'),
                'serializer': 'json',
                'sent': datetime.datetime.utcnow().isoformat(),
            }
        }
        producer.publish(payload)
        logger.warn('published pulse notification for %s' % repo_url)


def cli():
    """Command line interface to run the Pulse notification daemon."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file to load')
    args = parser.parse_args()

    config = Config(filename=args.config)

    if not config.c.has_section('pulse'):
        print('no [pulse] config section')
        sys.exit(1)

    group = config.c.get('pulseconsumer', 'group')
    topic = config.c.get('pulseconsumer', 'topic')

    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)s %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    client = config.get_client_from_section('pulseconsumer', timeout=5)
    consumer = Consumer(client, group, topic, partitions=None)

    cbkwargs = {
        'config': config,
    }
    run_in_loop(logger, consume_one, config=config, consumer=consumer,
                cb=on_push, cbkwargs=cbkwargs)
