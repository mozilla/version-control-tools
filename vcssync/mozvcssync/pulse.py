# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import socket

import kombu


class Consumer(object):
    """Represents a Pulse consumer to version control data."""
    def __init__(self, conn, github_exchange, hgmo_exchange, extra_data):
        self._conn = conn
        self._consumer = None
        self._entered = False
        self._github_exchange = github_exchange
        self._hgmo_exchange = hgmo_exchange
        self._extra_data = extra_data

        self.github_callbacks = []
        self.hgmo_callbacks = []

    def __enter__(self):
        self._consumer.consume()
        self._entered = True
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._consumer.cancel()
        self._entered = False

    def drain_events(self, timeout=0.1):
        """Drain all active events and call callbacks."""
        if not self._entered:
            raise Exception('must enter context manager before calling')

        try:
            self._conn.drain_events(timeout=timeout)
        except socket.timeout:
            pass

    def listen_forever(self):
        """Listen for and handle messages until interrupted."""
        if not self._entered:
            raise Exception('must enter context manager before calling')

        while True:
            try:
                self._conn.drain_events(timeout=1.0)
            except socket.timeout:
                pass

    def on_message(self, body, message):
        exchange = message.delivery_info['exchange']
        if exchange == self._github_exchange:
            for cb in self.github_callbacks:
                cb(body, message, self._extra_data)
        elif exchange == self._hgmo_exchange:
            for cb in self.hgmo_callbacks:
                cb(body, message, self._extra_data)
        else:
            raise Exception('received message from unknown exchange: %s' %
                            exchange)


def get_consumer(userid, password,
                 hostname='pulse.mozilla.org',
                 port=5571,
                 ssl=True,
                 github_exchange='exchange/github-webhooks/v1',
                 hgmo_exchange='exchange/hgpushes/v2',
                 github_queue=None,
                 hgmo_queue=None,
                 extra_data=None):
    """Obtain a Pulse consumer that can handle received messages.

    Caller passes Pulse connection details, including credentials. These
    credentials are managed at https://pulseguardian.mozilla.org/.

    Caller also passes one of ``github_queue`` and/or ``hgmo_queue`` defining
    the queue to "bind" to the GitHub and/or hg.mozilla.org event streams.
    At least one must be specified otherwise the consumer has nothing to
    listen to! This function prepends the ``queue/<userid>`` to the queue
    name per Pulse's naming requirements.

    Returns a ``Consumer`` instance bound to listen to the requested exchanges.
    Callers should append functions to the ``github_callbacks`` and/or
    ``hgmo_callbacks`` lists of this instance to register functions that will
    be called when a message is received.

    The returned ``Consumer`` must be active as a context manager for processing
    to work.

    The callback functions receive arguments ``body``, ``message``,
    and ``extra_data``. ``body`` is the decoded message body. ``message`` is
    the AMQP message from Pulse.  ``extra_data`` holds optional data for the
    consumers.

     **Callbacks must call ``message.ack()`` to acknowledge the message when
     done processing it.**
    """
    if not github_queue and not hgmo_queue:
        raise Exception('one of github_queue or hgmo_queue must be specified')

    if github_queue and github_queue.startswith('queue'):
        raise ValueError('github_queue must not start with "queue"')
    if hgmo_queue and hgmo_queue.startswith('queue'):
        raise ValueError('hgmo_queue must not start with "queue"')

    # Pulse requires queue names be prefixed with the userid. Do that
    # automatically.
    if github_queue:
        github_queue = 'queue/%s/%s' % (userid, github_queue)
    if hgmo_queue:
        hgmo_queue = 'queue/%s/%s' % (userid, hgmo_queue)

    conn = kombu.Connection(
        hostname=hostname,
        port=port,
        ssl=ssl,
        userid=userid,
        password=password)
    conn.connect()

    queues = []

    if github_queue:
        gh_exchange = kombu.Exchange(github_exchange, type='topic',
                                     channel=conn)
        gh_exchange.declare(passive=True)

        gh_queue = kombu.Queue(name=github_queue,
                               exchange=gh_exchange,
                               durable=True,
                               routing_key='#',
                               exclusive=False,
                               auto_delete=False,
                               channel=conn)
        queues.append(gh_queue)

    if hgmo_queue:
        hg_exchange = kombu.Exchange(hgmo_exchange, type='topic',
                                     channel=conn)
        hg_exchange.declare(passive=True)

        hg_queue = kombu.Queue(name=hgmo_queue,
                               exchange=hg_exchange,
                               durable=True,
                               routing_key='#',
                               exclusive=False,
                               auto_delete=False,
                               channel=conn)
        queues.append(hg_queue)

    consumer = Consumer(conn, github_exchange, hgmo_exchange, extra_data)
    kombu_consumer = conn.Consumer(queues, callbacks=[consumer.on_message],
                                   auto_declare=False)
    consumer._consumer = kombu_consumer

    # queue.declare() declares the exchange, which isn't allowed by the
    # server. So call the low-level APIs to only declare the queue itself.
    for queue in kombu_consumer.queues:
        queue.queue_declare()
        queue.queue_bind()

    return consumer
