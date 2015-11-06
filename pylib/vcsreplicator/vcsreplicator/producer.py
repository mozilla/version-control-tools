# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging

from kafka.producer.base import Producer as KafkaProducer


logger = logging.getLogger(__name__)


class Producer(KafkaProducer):
    """A Kafka Producer that writes to a pre-defined topic and partition."""

    def __init__(self, client, topic, partition, **kwargs):
        super(Producer, self).__init__(client, **kwargs)

        self.topic = topic
        self.partition = partition

    def send_message(self, o):
        """Send a single message from a Python object."""

        # We currently only support 1 message format. It is
        # "1\n" followed by a JSON payload. No length is encoded,
        # as Kafka does this for us.
        j = json.dumps(o, sort_keys=True)
        msg = b'1\n%s' % j

        return super(Producer, self).send_messages(
            self.topic, self.partition, msg)


def send_heartbeat(producer):
    """Sends a dummy message to confirm that the queue is running."""
    return producer.send_message({
        'name': 'heartbeat-1',
    })


def record_new_hg_repo(producer, path):
    """Produce a message saying a Mercurial repository was created.

    This should be called when a new repository is to become under the
    control of the replication service.

    When this message is received by consumers, it is equivalent to
    cloning the repository.
    """
    return producer.send_message({
        'name': 'hg-repo-init-1',
        'path': path,
    })


def record_hgrc_update(producer, path, content):
    """Produce a message saying a Mercurial config file was updated.

    When called, the passed hgrc content will be written along with the
    path to the repository. Mirrors are expected to overwrite the
    repository's hgrc with the content provided.

    If content is None, an existing hgrc file will be deleted.
    """
    return producer.send_message({
        'name': 'hg-hgrc-update-1',
        'path': path,
        'content': content,
    })
