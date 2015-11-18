# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import time

from kafka.producer.base import Producer as KafkaProducer


logger = logging.getLogger(__name__)


class Producer(KafkaProducer):
    """A Kafka Producer that writes to a pre-defined topic."""

    def __init__(self, client, topic, **kwargs):
        super(Producer, self).__init__(client, **kwargs)

        self.topic = topic

    def send_message(self, o, partition):
        """Send a single message from a Python object.

        The partition, if specified, overwrites whatever the default partition
        is configured as.
        """
        # Add the message created time to all messages. This is used to monitor
        # latency.
        o['_created'] = time.time()
        # We currently only support 1 message format. It is
        # "1\n" followed by a JSON payload. No length is encoded,
        # as Kafka does this for us.
        j = json.dumps(o, sort_keys=True)
        msg = b'1\n%s' % j

        return super(Producer, self).send_messages(
            self.topic, partition, msg)


def send_heartbeat(producer, partition):
    """Sends a dummy message to confirm that the queue is running."""
    return producer.send_message({
        'name': 'heartbeat-1',
    }, partition=partition)


def record_new_hg_repo(producer, path, partition):
    """Produce a message saying a Mercurial repository was created.

    This should be called when a new repository is to become under the
    control of the replication service.

    When this message is received by consumers, it is equivalent to
    cloning the repository.
    """
    return producer.send_message({
        'name': 'hg-repo-init-1',
        'path': path,
    }, partition=partition)


def record_hgrc_update(producer, path, content, partition):
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
    }, partition=partition)


def record_hg_changegroup(producer, path, source, nodes, heads,
                          partition):
    """Produce a message saying a changegroup has been added to the repository.

    The message records a list of introduced changesets, which ones are heads,
    and the source of the changesets (as reported by Mercurial).
    """
    return producer.send_message({
        'name': 'hg-changegroup-1',
        'path': path,
        'source': source,
        'nodes': nodes,
        'heads': heads,
    }, partition=partition)


def record_hg_pushkey(producer, path, namespace, key, old, new, ret,
        partition):
    """Produce a message saying that a pushkey change was processed."""
    return producer.send_message({
        'name': 'hg-pushkey-1',
        'path': path,
        'namespace': namespace,
        'key': key,
        'old': old,
        'new': new,
        'ret': ret,
    }, partition=partition)

def record_hg_repo_sync(producer, path, hgrc, heads, requirements, partition):
    """Produce a message that will synchronize a repository."""
    return producer.send_message({
        'name': 'hg-repo-sync-1',
        'path': path,
        'requirements': sorted(list(requirements)),
        'hgrc': hgrc,
        'heads': heads,
    }, partition=partition)
