# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import copy
import functools
import logging
import os
import time


from kafka.common import OffsetRequestPayload as OffsetRequest
from kafka.consumer.base import Consumer
from kafka.errors import UnknownTopicOrPartitionError


# Retry policy used by `retry_on_failure`. Values may be overridden at
# process startup via environment variables; tests set
# `VCSREPLICATOR_RETRY_MAX_RETRIES=0` so failure-path assertions don't
# incur the production retry sleep (2+4+8+16+32 = 62s per failed message).
RETRY_MAX_RETRIES = int(os.environ.get("VCSREPLICATOR_RETRY_MAX_RETRIES", 5))
RETRY_BASE_DELAY = int(os.environ.get("VCSREPLICATOR_RETRY_BASE_DELAY", 2))

# Exceptions that retry cannot fix — programming errors and malformed
# payloads. These bypass retry so poison messages exit the daemon
# quickly (where the systemd burst limiter can trip `failed` state)
# instead of burning the full retry budget on every redelivery.
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,
    KeyError,
    TypeError,
    AssertionError,
)


class ShutDownException(Exception):
    """Raised to unwind a Kafka consume loop in response to SIGINT/SIGTERM.

    Lives at module scope so the ``retry_on_failure`` decorator can
    re-raise it without treating it as a retryable failure.
    """


def retry_on_failure(fn):
    """Retry a Kafka message-handler call on transient exceptions with exponential backoff.

    On a transient exception from ``fn``, the call is retried up to
    ``RETRY_MAX_RETRIES`` additional times. The delay before the n-th
    retry (0-indexed) is ``RETRY_BASE_DELAY * 2**n`` seconds. After
    retries are exhausted the exception propagates, which (in the
    typical consumer topology) leaves the Kafka offset uncommitted and
    exits the daemon, so systemd will restart it and re-deliver the
    same message.

    Exceptions in ``NON_RETRYABLE_EXCEPTIONS`` (programming errors,
    malformed payloads) are re-raised immediately so poison messages
    exit the daemon quickly rather than spinning in-process.

    ``ShutDownException`` is re-raised without retry so signal-driven
    shutdown during a retry sleep terminates the daemon cleanly.
    """
    module_logger = logging.getLogger(fn.__module__)

    @functools.wraps(fn)
    def retrywrapper(*args, **kwargs):
        for attempt in range(RETRY_MAX_RETRIES + 1):
            try:
                return fn(*args, **kwargs)
            except ShutDownException:
                raise
            except NON_RETRYABLE_EXCEPTIONS as exc:
                module_logger.error(
                    "%s failed with non-retryable exception: %s: %s"
                    % (fn.__name__, type(exc).__name__, exc)
                )
                raise
            except Exception as exc:
                if attempt >= RETRY_MAX_RETRIES:
                    if RETRY_MAX_RETRIES == 0:
                        module_logger.error(
                            "%s failed (retries disabled): %s: %s"
                            % (fn.__name__, type(exc).__name__, exc)
                        )
                    else:
                        module_logger.error(
                            "%s failed after %d attempts: %s: %s"
                            % (
                                fn.__name__,
                                attempt + 1,
                                type(exc).__name__,
                                exc,
                            )
                        )
                    raise

                delay = RETRY_BASE_DELAY * (2 ** attempt)
                module_logger.warning(
                    "%s failed (%s: %s); retrying in %ds "
                    "(attempt %d of %d)"
                    % (
                        fn.__name__,
                        type(exc).__name__,
                        exc,
                        delay,
                        attempt + 1,
                        RETRY_MAX_RETRIES,
                    )
                )
                time.sleep(delay)

    return retrywrapper

PAYLOAD_LOGS = {
    "hg-repo-init-1": "repo: {path}",
    "hg-repo-init-2": "repo: {path}",
    "hg-hgrc-update-1": "repo: {path}",
    "hg-changegroup-1": "repo: {path}, heads: {heads}",
    "hg-changegroup-2": "repo: {path}, heads: {heads}",
    "hg-pushkey-1": "repo: {path}, namespace/key: {namespace}/{key}",
    "hg-repo-sync-1": "repo: {path}, heads: {heads}",
    "hg-repo-sync-2": "repo: {path}, heads: {heads}, bootstrap: {bootstrap}",
    "hg-heads-1": "repo: {path}, heads: {heads}, last_push_id: {last_push_id}",
    "hg-repo-delete-1": "repo: {path}",
}

MAX_HEADS_PER_MESSAGE = 25


def payload_log_display(payload):
    """Return a string that adds information about the payload for use in logs."""
    name = payload["name"]
    if name == "heartbeat-1":
        return "heartbeat-1"

    if "heads" in payload:
        # Deepcopy because we don't want to modify the original payload.
        payload = copy.deepcopy(payload)

        # Print only the short version of the hash.
        payload["heads"] = [head[:12] for head in payload["heads"]]

        # Enforce a maximum number of heads per message.
        num_heads = len(payload["heads"])
        if num_heads > MAX_HEADS_PER_MESSAGE:
            payload["heads"] = "{heads} and {remaining} more".format(
                heads=payload["heads"][:MAX_HEADS_PER_MESSAGE],
                remaining=num_heads - MAX_HEADS_PER_MESSAGE,
            )

    return "{}: ({})".format(name, PAYLOAD_LOGS[name].format(**payload))


def wait_for_topic(client, topic, timeout=-1):
    """Wait for a topic to exist on a Kafka connection.

    Sometimes there is a race condition between establishing a Kafka client
    and a topic being created. This function exists to have the client wait for
    a topic to exist before proceeding.
    """
    start = time.time()
    while True:
        if timeout > 0 and time.time() - start > timeout:
            raise Exception("timeout reached waiting for topic")

        # Don't pass topic name to function or it will attempt to create it.
        client.load_metadata_for_topics()

        if not client.has_metadata_for_topic(topic):
            time.sleep(0.1)
            continue

        # Verify that the topic is also accessible via a targeted fetch, which
        # is what Consumer.__init__ will do. There is a brief window where the
        # full refresh reports success but the targeted fetch still raises
        # UnknownTopicOrPartitionError (e.g. during leader election on newer
        # Kafka versions).
        try:
            client.load_metadata_for_topics(topic, ignore_leadernotavailable=True)
            break
        except UnknownTopicOrPartitionError:
            time.sleep(0.1)
            continue


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
    res = {"group": {}}

    offsets = fetch_partition_offsets(client, topic)
    res["available"] = offsets

    for group in groups:
        consumer = Consumer(
            client, group, topic, partitions=offsets.keys(), auto_commit=False
        )
        res["group"][group] = dict(consumer.offsets)

    return res
