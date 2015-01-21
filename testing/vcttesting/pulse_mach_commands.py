# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import socket
import yaml

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

@CommandProvider
class PulseCommands(object):
    def _get_connection(self):
        from kombu import Connection

        pulse_host = None
        pulse_port = None

        if 'PULSE_HOST' in os.environ:
            pulse_host = os.environ['PULSE_HOST']
        if 'PULSE_PORT' in os.environ:
            pulse_port = int(os.environ['PULSE_PORT'])

        if not pulse_host:
            raise Exception('Can not find Pulse host. Try setting PULSE_HOST')
        if not pulse_port:
            raise Exception('Can not find Pulse port. Try setting PULSE_PORT')

        return Connection(hostname=pulse_host, port=pulse_port,
            userid='guest', password='guest', ssl=False)

    def _get_queue(self, exchange, queue):
        from kombu import Exchange, Queue

        e = Exchange(exchange, type='topic', durable=True)
        q = Queue(name=queue, exchange=e, durable=True,
                routing_key='#', exclusive=False, auto_delete=False)

        return e, q

    @Command('create-queue', category='pulse',
        description='Create a queue')
    @CommandArgument('exchange', help='Name of exchange to create on')
    @CommandArgument('queue', help='Name of queue to create')
    def create_exchange(self, exchange, queue):
        conn = self._get_connection()
        e, q = self._get_queue(exchange, queue)
        e(conn).declare(passive=False)
        conn.Consumer([q], auto_declare=True)

    @Command('dump-messages', category='pulse',
        description='Dump all messages on a queue')
    @CommandArgument('exchange', help='Exchange to read from')
    @CommandArgument('queue', help='Queue to read from')
    def dump_messages(self, exchange, queue):
        conn = self._get_connection()
        e, q = self._get_queue(exchange, queue)

        data = []

        def onmessage(body, message):
            d = {
                '_meta': {
                    'exchange': body['_meta']['exchange'],
                    'routing_key': body['_meta']['routing_key'],
                },
            }
            for k, v in body['payload'].iteritems():
                d[k] = v

            data.append(d)

        with conn.Consumer([q], callbacks=[onmessage], auto_declare=False):
            try:
                conn.drain_events(timeout=0.1)
            except socket.timeout:
                pass

        print(yaml.safe_dump(data, default_flow_style=False).rstrip())
