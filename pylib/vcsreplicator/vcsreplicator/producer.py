# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import time

from mercurial import (
    pycompat,
)

from kafka.producer.base import Producer as KafkaProducer
from kafka.common import KafkaError


logger = logging.getLogger("kafka.producer")

MESSAGE_HEADER_V1 = b"1\n"


class Producer(KafkaProducer):
    """A Kafka Producer that writes to a pre-defined topic."""

    def __init__(self, client, topic, **kwargs):
        super(Producer, self).__init__(client, **kwargs)

        self.topic = topic

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def send_message(self, o, partition):
        """Send a single message from a Python object.

        The partition, if specified, overwrites whatever the default partition
        is configured as.
        """
        # Add the message created time to all messages. This is used to monitor
        # latency.
        o["_created"] = time.time()
        # We currently only support 1 message format. It is
        # "1\n" followed by a JSON payload. No length is encoded,
        # as Kafka does this for us.
        j = pycompat.bytestr(json.dumps(o, sort_keys=True))
        msg = b"".join([MESSAGE_HEADER_V1, j])

        try:
            return super(Producer, self).send_messages(self.topic, partition, msg)

        except KafkaError:
            logger.exception(
                "error sending message to Kafka; reinitializing client to retry"
            )
            self.client.reinit()

            return super(Producer, self).send_messages(self.topic, partition, msg)


def send_heartbeat(producer, partition):
    """Sends a dummy message to confirm that the queue is running."""
    return producer.send_message(
        {
            "name": "heartbeat-1",
        },
        partition=partition,
    )


def record_new_hg_repo(producer, path, partition, generaldelta=False):
    """Produce a message saying a Mercurial repository was created.

    This should be called when a new repository is to become under the
    control of the replication service.

    When this message is received by consumers, it is equivalent to
    cloning the repository.
    """
    return producer.send_message(
        {
            "name": "hg-repo-init-2",
            "path": path,
            "generaldelta": generaldelta,
        },
        partition=partition,
    )


def record_hgrc_update(producer, path, content, partition):
    """Produce a message saying a Mercurial config file was updated.

    When called, the passed hgrc content will be written along with the
    path to the repository. Mirrors are expected to overwrite the
    repository's hgrc with the content provided.

    If content is None, an existing hgrc file will be deleted.
    """
    return producer.send_message(
        {
            "name": "hg-hgrc-update-1",
            "path": path,
            "content": content,
        },
        partition=partition,
    )


def record_hg_changegroup(producer, path, source, nodes, heads, partition):
    """Produce a message saying a changegroup has been added to the repository.

    The message records a list of introduced changesets, which ones are heads,
    and the source of the changesets (as reported by Mercurial).
    """
    return producer.send_message(
        {
            "name": "hg-changegroup-2",
            "path": path,
            "source": source,
            "nodecount": len(nodes),
            "heads": heads,
        },
        partition=partition,
    )


def record_hg_pushkey(producer, path, namespace, key, old, new, ret, partition):
    """Produce a message saying that a pushkey change was processed."""
    return producer.send_message(
        {
            "name": "hg-pushkey-1",
            "path": path,
            "namespace": namespace,
            "key": key,
            "old": old,
            "new": new,
            "ret": ret,
        },
        partition=partition,
    )


def record_hg_repo_sync(
    producer, path, hgrc, heads, requirements, partition, bootstrap=False
):
    """Produce a message that will synchronize a repository."""
    return producer.send_message(
        {
            "name": "hg-repo-sync-2",
            "path": path,
            "requirements": sorted(i for i in list(requirements)),
            "hgrc": hgrc,
            "heads": heads,
            "bootstrap": bootstrap,
        },
        partition=partition,
    )


def record_hg_repo_heads(producer, path, heads, last_push_id, partition):
    """Produce a message that advertises heads in a repository."""
    return producer.send_message(
        {
            "name": "hg-heads-1",
            "path": path,
            "heads": heads,
            "last_push_id": last_push_id,
        },
        partition=partition,
    )


def record_hg_repo_delete(producer, path, partition):
    """Produce a message that will delete a repository."""
    return producer.send_message(
        {
            "name": "hg-repo-delete-1",
            "path": path,
        },
        partition=partition,
    )
