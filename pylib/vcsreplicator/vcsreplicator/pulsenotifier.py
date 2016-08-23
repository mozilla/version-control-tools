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


def send_pulse_message(config, exchange, repo_url, payload):
    """Send a pulse message for a repository event.

    The Pulse host configured by the config object will be connected to.
    The routing key will be constructed from the repository URL.
    The Pulse message will be constructed from the specified payload
    and sent to the requested exchange.
    """
    c = config.c

    routing_key_strip_prefix = c.get('pulse', 'routing_key_strip_prefix')
    if not repo_url.startswith(routing_key_strip_prefix):
        raise Exception('repo URL does not begin with %s: %s' % (
            routing_key_strip_prefix, repo_url))

    routing_key = repo_url[len(routing_key_strip_prefix):]

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
        ex = kombu.Exchange(exchange, type='topic')
        producer = conn.Producer(exchange=ex,
                                 routing_key=routing_key,
                                 serializer='json')

        data = {
            'payload': payload,
            '_meta': {
                'exchange': exchange,
                'routing_key': routing_key,
                'serializer': 'json',
                'sent': datetime.datetime.utcnow().isoformat(),
            }
        }

        producer.publish(data)
        logger.warn('published pulse notification for %s' % repo_url)


def on_event(config, message_type, data):
    """Called when a replication message should be handled."""
    repo_url = data['repo_url']
    logger.warn('sending pulse notification for %s' % repo_url)

    # v1 of the exchange only supported a single message type that corresponded
    # to ``changegroup.1`` messages. So only send these messages to that
    # exchange.
    if message_type == 'changegroup.1':
        # ``source`` wasn't sent to the v1 exchange. Strip it.
        del data['source']

        exchange = config.c.get('pulse', 'exchange')
        send_pulse_message(config, exchange, repo_url, data)


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

    with Consumer(client, group, topic, partitions=None) as consumer:
        cbkwargs = {
            'config': config,
        }
        res = run_in_loop(logger, consume_one, config=config, consumer=consumer,
                          cb=on_event, cbkwargs=cbkwargs)

    logger.warn('process exiting code %s' % res)
    sys.exit(res)
