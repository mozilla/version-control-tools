# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import Queue

import kombu


class NoQueueDefined(RuntimeError):
    """Exception raised when trying to consume with no queue."""
    pass


class FIFOPulseConsumer(object):
    """A pulse consumer which consumes in FIFO order.

    This consumer is designed to be the sole consumer of
    a pulse queue. If other processes are able to consume
    from the queue at the same there is no guarantee of
    FIFO processing of the queue.

    In the event that processing of a message cannot be
    completed, but it should be retried as the next
    message of the queue, the callback should not ack
    or reject the message. An ignored message will
    stay at the head of the queue until it is rejected
    or acked.

    Messages should never be requeued (also known as
    rejected with requeue), since the delivery mechanics
    are not as well defined and it could violate FIFO
    ordering. Instead the message should not be acked
    or nacked, which will cause it to be processed again
    as previously mentioned.
    """

    def __init__(self, host, port, userid=None, password=None,
                 ssl=False, timeout=1.0, exchange=None, queue=None,
                 routing_key=None, callback=None, logger=None, **kwargs):
        """Initialize the consumer.

        Args:
            host (str): The Pulse hostname.
            port (int): The Pulse server port.
            userid (str): The Pulse user to authenticate as.
            password (str): The Pulse user password for authentication.
            ssl (bool): Should ssl be used when connection to Pulse.
            timeout (float): The timeout in seconds to use when fetching
                messages from the Pulse server.
            exchange (str): The Pulse exchange name where messages are
                produced.
            queue (str): The Pulse queue to consume from.
            routing_key (str): The routing key to use for the queue.
            callback (callable): A callable to be called for each message. The
                callable will be passed the message as the first argument, and
                the consumer instance through the `consumer` kwarg.
            logger (logging.Logger): The logger to use for logging.
        """
        self.host = host
        self.port = port
        self.userid = userid
        self.password = password
        self.ssl = ssl
        self.timeout = float(timeout)

        self.exchange = exchange
        self.queue = queue
        self.routing_key = routing_key
        self.callback = callback

        self.logger = logger or logging.getLogger(__name__)

    def _create_connection(self):
        """Create a kombu.Connection."""
        return kombu.Connection(
            hostname=self.host, port=self.port, userid=self.userid,
            password=self.password, ssl=self.ssl)

    def _create_simple_queue(self, connection):
        """Create a kombu.SimpleQueue from a kombu.Connection."""
        exchange = kombu.Exchange(
            self.exchange, type='topic', durable=True, passive=True)
        queue = kombu.Queue(
            name=self.queue, exchange=exchange,
            durable=True, routing_key=self.routing_key,
            exclusive=False, auto_delete=False)
        return connection.SimpleQueue(queue)

    def _process_message(self, msg, connection, simple_queue):
        """Process a message.

        Return True if the consumer must reconnect before
        consuming another message or False if the consumer
        is fine to continue with the same connection.
        """
        self.callback(msg, consumer=self)
        self._processed += 1

        # If the callback did not ack/nack the message we
        # must reconnect before consuming another message
        # so that the same message is redelivered.
        #
        # We could deal with requeuing in the same way, but
        # differentiating between a requeue and the other
        # ack states requires touching "private" properties
        # of the message. It would not provide any meaningful
        # extra functionality though, since it would act the
        # same as unacknowledged messages after a reconnect.
        return not msg.acknowledged

    def _consume(self, connection, limit=None):
        """Attempt to consume a number of messages.

        Return True if consuming should continue or False if
        it should stop.
        """
        simple_queue = self._create_simple_queue(connection)

        try:
            while limit is None or self._processed < limit:
                try:
                    msg = simple_queue.get(timeout=self.timeout)
                except Queue.Empty:
                    if limit is not None:
                        return False
                    else:
                        continue

                if self._process_message(msg, connection, simple_queue):
                    # We must reconnect so that we reconsume
                    # this message again.
                    return True

        except connection.recoverable_connection_errors:
            pass
        except connection.connection_errors:
            # TODO: Should we implement some sort of backoff
            # for these irrecoverable errors? For now ignore
            # them and just keep trying to connect in
            # consume()
            pass

        return True

    def consume(self, limit=None):
        """Consume pulse messages.

        If a `limit` is provided a `limit` number of messages will be
        consumed or consumption will stop when the queue is empty,
        whichever comes first. Otherwise, `consumer` will block and wait
        for messages, consuming indefinitely.

        The number of messages processed in a call to consume
        will be returned.
        """
        self._processed = 0

        while limit is None or self._processed < limit:
            connection = self._create_connection()

            with connection.ensure_connection() as connection:
                if not self._consume(connection, limit=limit):
                    break

        return self._processed
