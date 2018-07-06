# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import shutil
import time


from kafka.common import OffsetRequestPayload as OffsetRequest
from kafka.consumer.base import Consumer


def wait_for_topic(client, topic, timeout=-1):
    """Wait for a topic to exist on a Kafka connection.

    Sometimes there is a race condition between establishing a Kafka client
    and a topic being created. This function exists to have the client wait for
    a topic to exist before proceeding.
    """
    start = time.time()
    while not client.has_metadata_for_topic(topic):
        if timeout > 0 and time.time() - start > timeout:
            raise Exception('timeout reached waiting for topic')

        time.sleep(0.1)

        # Don't pass topic name to function or it will attempt to create it.
        client.load_metadata_for_topics()


def fetch_partition_offsets(client, topic):
    """Fetch partition offsets for a topic.

    Given a client and a topic, return a dict mapping the partition number to
    total available messages in that partition.
    """
    client.load_metadata_for_topics(topic)
    reqs = []
    for p in sorted(client.topic_partitions[topic].keys()):
        reqs.append(OffsetRequest(topic, p, -1, 1))

    resps = client.send_offset_request(reqs)
    res = {}
    for resp in resps:
        res[resp.partition] = resp.offsets[0]

    return res


def consumer_offsets(client, topic, groups):
    """Fetch consumer offsets for a given topic.

    Given a client, topic, and iterable of group names, return a data
    structure describing the state of the topic, its partitions, and how
    far each group has consumed into each.

    Returns a dict with keys:

    available
       A dict of integer partition to available messages in partition.
    group
       A dict of group name to dict of partition to consumed offset.

    Because there is no way to atomically fetch all data, the consumed offset
    for a group may be larger than the listed available offset in the
    partition.
    """
    res = {'group': {}}

    offsets = fetch_partition_offsets(client, topic)
    res['available'] = offsets

    for group in groups:
        consumer = Consumer(client, group, topic, partitions=offsets.keys(),
                auto_commit=False)
        res['group'][group] = dict(consumer.offsets)

    return res
