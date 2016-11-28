# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Pulse Consumer tests.
"""
import pytest

from mozreviewpulse.consumer import FIFOPulseConsumer


class MessageCollector(list):
    def clear(self):
        del self[:]

    def ack_callback(self, message, consumer=None, *args, **kwargs):
        self.append(message)
        message.ack()

    def reject_callback(self, message, consumer=None, *args, **kwargs):
        self.append(message)
        message.reject()

    def requeue_callback(self, message, consumer=None, *args, **kwargs):
        self.append(message)
        message.requeue()

    def ignore_callback(self, message, consumer=None, *args, **kwargs):
        self.append(message)
        # Don't ack or reject the message.

    def id_for(self, i):
        return self[i].payload['id']


def build_consumer(producer, queue, routing_key='testmessage',
                   consumer_class=FIFOPulseConsumer, **kwargs):
    """Construct a consumer for the provided producer.

    The consumer should be created before producing any
    messages.
    """
    msgs = MessageCollector()
    consumer = consumer_class(
        host=producer.connection.hostname,
        port=producer.connection.port or 5672,
        exchange=producer.exchange.name,
        queue=queue,
        routing_key=routing_key,
        callback=msgs.ack_callback,
        **kwargs)

    # attempt to consume a single message, which will timeout,
    # so that our queue is declared.
    assert consumer.consume(limit=1) == 0
    assert len(msgs) == 0
    return consumer, msgs


def produce_incrementing_messages(producer, n, routing_key='testmessage'):
    """Publish n messages with incrementing ids on the producer."""
    for i in xrange(n):
        producer.publish({'id': i}, routing_key=routing_key, retry=True)


def test_limit_messages_consumed(pulse_producer):
    consumer, msgs = build_consumer(pulse_producer,
                                    'limit_messages_consumed_queue')

    # Produce a few messages that we can consume.
    produce_incrementing_messages(pulse_producer, 3)

    # We should only consume a single message if we set the limit
    # to 1.
    assert consumer.consume(limit=1) == 1
    assert len(msgs) == 1

    # When the limit is higher than the number of messages in
    # the queue, consumption will stop when the queue is empty.
    assert consumer.consume(limit=10) == 2
    assert len(msgs) == 3


def test_fifo_ack_removes_message(pulse_producer):
    consumer, msgs = build_consumer(pulse_producer,
                                    'fifo_ack_removes_message_queue')
    produce_incrementing_messages(pulse_producer, 2)

    consumer.callback = msgs.ack_callback
    assert consumer.consume(limit=1) == 1
    assert consumer.consume(limit=1) == 1
    assert len(msgs) == 2

    # The two messages consumed are not duplicates.
    assert msgs.id_for(0) != msgs.id_for(1)
    assert msgs.id_for(0) == 0
    assert msgs.id_for(1) == 1


def test_fifo_reject_removes_message(pulse_producer):
    consumer, msgs = build_consumer(pulse_producer,
                                    'fifo_reject_removes_message_queue')
    produce_incrementing_messages(pulse_producer, 2)

    consumer.callback = msgs.reject_callback
    assert consumer.consume(limit=1) == 1
    assert consumer.consume(limit=1) == 1
    assert len(msgs) == 2

    # The two messages consumed are not duplicates.
    assert msgs.id_for(0) != msgs.id_for(1)
    assert msgs.id_for(0) == 0
    assert msgs.id_for(1) == 1


def test_fifo_ignore_redelivers_message(pulse_producer):
    consumer, msgs = build_consumer(pulse_producer,
                                    'fifo_ignore_redelivers_message_queue')
    produce_incrementing_messages(pulse_producer, 2)
    consumer.callback = msgs.ignore_callback

    # We should be able to consume many more messages
    # than there are currently queued since the same
    # message should be redelivered every time it
    # is not acked.
    assert consumer.consume(limit=20) == 20

    # The same message should have been delivered
    # every time.
    for i, msg in enumerate(msgs):
        assert msgs.id_for(i) == msgs.id_for(1)

    # Clear the messages and consume one more as
    # that's all we really need.
    msgs.clear()
    assert consumer.consume(limit=1) == 1
    assert len(msgs) == 1

    # Acking should actually take the message off
    # the queue now.
    consumer.callback = msgs.ack_callback
    assert consumer.consume(limit=2) == 2
    assert len(msgs) == 3

    # The second message should match the previously
    # ignored message, but since it was acked the
    # third message should not be a duplicate.
    assert msgs.id_for(1) == msgs.id_for(0)
    assert msgs.id_for(1) != msgs.id_for(2)

    # The queue should be empty now.
    assert consumer.consume(limit=1) == 0


@pytest.mark.skip(reason="Properly handling requeue would require touching "
                         "private properties of the message. Ignoring the "
                         "message can be used in practice instead.")
def test_fifo_requeue_redelivers_message(pulse_producer):
    consumer, msgs = build_consumer(pulse_producer,
                                    'fifo_requeue_redelivers_message_queue')
    produce_incrementing_messages(pulse_producer, 2)
    consumer.callback = msgs.requeue_callback

    # We should be able to consume many more messages
    # than there are currently queued since the same
    # message should be redelivered every time it
    # is requeued.
    assert consumer.consume(limit=20) == 20

    # The same message should have been delivered
    # every time.
    for i, msg in enumerate(msgs):
        assert msgs.id_for(i) == msgs.id_for(1)

    # Clear the messages and consume one more as
    # that's all we really need.
    msgs.clear()
    assert consumer.consume(limit=1) == 1
    assert len(msgs) == 1

    # Acking should actually take the message off
    # the queue now.
    consumer.callback = msgs.ack_callback
    assert consumer.consume(limit=2) == 2
    assert len(msgs) == 3

    # The second message should match the previously
    # requeued message, but since it was acked the
    # third message should not be a duplicate.
    assert msgs.id_for(1) == msgs.id_for(0)
    assert msgs.id_for(1) != msgs.id_for(2)

    # The queue should be empty now.
    assert consumer.consume(limit=1) == 0

