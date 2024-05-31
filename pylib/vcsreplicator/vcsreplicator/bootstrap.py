# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import json
import logging
import multiprocessing
import subprocess
import sys
import time

import concurrent.futures as futures

import hglib

from hgmolib import find_hg_repos
from kafka import (
    KafkaConsumer,
    OffsetAndMetadata,
    TopicPartition,
)

from .config import Config
from .consumer import (
    value_deserializer,
    process_hg_sync,
    handle_message_main,
    MAX_BUFFER_SIZE,
)


REPOS_DIR = "/repo/hg/mozilla"

formatter = logging.Formatter(
    "%(asctime)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
formatter.converter = time.gmtime

logger = logging.getLogger("vcsreplicator.bootstrap")
main_file_handler = logging.FileHandler("/var/log/vcsrbootstrap/bootstrap.log")
main_file_handler.setFormatter(formatter)
main_stdout_handler = logging.StreamHandler(sys.stdout)
main_stdout_handler.setFormatter(formatter)
logger.addHandler(main_file_handler)
logger.addHandler(main_stdout_handler)
logger.setLevel(logging.INFO)

# Send vcsreplicator consumer logs to a separate file
consumer_logger = logging.getLogger("vcsreplicator.consumer")
consumer_handler = logging.FileHandler("/var/log/vcsrbootstrap/consumer.log")
consumer_logger.addHandler(consumer_handler)

# Send kafka-python logs to a separate file
kafka_logger = logging.getLogger("kafka")
kafka_handler = logging.FileHandler("/var/log/vcsrbootstrap/kafka.log")
kafka_handler.setLevel(logging.DEBUG)
kafka_logger.addHandler(kafka_handler)


def clone_repo(config, path, requirements, hgrc, heads):
    """Wraps process_hg_sync to provide logging"""
    logger.info("syncing repo: %s" % path)
    try:
        return process_hg_sync(config, path, requirements, hgrc, heads, create=True)
    finally:
        logger.info("exiting sync for: %s" % path)


def seqmap(message_handler, events):
    """Process events using the message handler in the order they
    arrived in the queue
    """
    for config, payload in events:
        message_handler(config, payload)


def hgssh():
    """hgssh component of the vcsreplicator bootstrap procedure."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config file")
    parser.add_argument("hg", help="Path to hg executable for use in bootstrap process")
    parser.add_argument(
        "--workers",
        help="Number of concurrent workers to use for publishing messages",
        type=int,
        default=multiprocessing.cpu_count(),
    )
    parser.add_argument("--output", help="Output file path for hgssh JSON")
    args = parser.parse_args()

    config = Config(filename=args.config)

    topic = config.c.get("replicationproducer", "topic")

    # Create consumer to gather partition offsets
    consumer_config = {
        # set this so offsets are committed to Zookeeper
        "api_version": (0, 8, 1),
        "bootstrap_servers": [
            host.strip()
            for host in config.c.get("replicationproducer", "hosts").split(",")
        ],
        "enable_auto_commit": False,  # We don't actually commit but this is just for good measure
    }
    consumer = KafkaConsumer(**consumer_config)

    # This call populates topic metadata for all topics in the cluster.
    # Needed as missing topic metadata can cause the below call to retrieve
    # partition information to fail.
    consumer.topics()

    partitions = consumer.partitions_for_topic(topic)
    if not partitions:
        logger.critical("could not get partitions for %s" % topic)
        sys.exit(1)

    # Gather the initial offsets
    topicpartitions = [
        TopicPartition(topic, partition_number)
        for partition_number in sorted(partitions)
    ]
    offsets_start = consumer.end_offsets(topicpartitions)
    logger.info("gathered initial Kafka offsets")

    # Mapping of `replicatesync` future to corresponding repo name
    replicatesync_futures = {}
    with futures.ThreadPoolExecutor(args.workers) as e:
        # Create a future which makes a `replicatesync` call
        # for each repo on hg.mo
        for repo in find_hg_repos(REPOS_DIR):
            # Create a future to call `replicatesync` for this repo
            replicatesync_args = [
                args.hg,
                "-R",
                repo,
                "replicatesync",
                "--bootstrap",
            ]
            replicatesync_futures.update(
                {e.submit(subprocess.check_output, replicatesync_args): repo}
            )

            logger.info("calling `replicatesync --bootstrap` on %s" % repo)

        # Execute the futures and raise an Exception on fail
        for future in futures.as_completed(replicatesync_futures):
            repo = replicatesync_futures[future]

            exc = future.exception()
            if exc:
                logger.error(
                    "error occurred calling `replicatesync --bootstrap` on %s: %s"
                    % (repo, exc)
                )
                raise Exception(
                    "error triggering replication of Mercurial repo %s: %s"
                    % (repo, exc)
                )
            logger.info("called `replicatesync --bootstrap` on %s successfully" % repo)

    # Gather the final offsets
    offsets_end = consumer.end_offsets(topicpartitions)
    logger.info("gathered final Kafka offsets")

    # Create map of partition numbers to (start, end) offset tuples
    offsets_combined = {
        int(topicpartition.partition): (
            offsets_start[topicpartition],
            offsets_end[topicpartition],
        )
        for topicpartition in topicpartitions
    }

    # Create JSON for processing in ansible and print to stdout
    # Convert repo paths into their wire representations
    output = {
        "offsets": offsets_combined,
        "repositories": sorted(
            [
                config.get_replication_path_rewrite(repo)
                for repo in replicatesync_futures.values()
            ]
        ),
    }

    print(json.dumps(output, sort_keys=True))
    logger.info("hgssh bootstrap process complete!")

    # Send output to a file if requested
    if args.output:
        logger.info("writing output to %s" % args.output)
        with open(args.output, "w") as f:
            json.dump(output, f)


def hgweb():
    """hgweb component of the vcsreplicator bootstrap procedure. Takes a
    vcsreplicator config path on the CLI and takes a JSON data structure
    on stdin"""
    import argparse

    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path of config file to load")
    parser.add_argument(
        "input",
        help="JSON data input (output from the hgssh bootstrap procedure) file path",
    )
    parser.add_argument(
        "--workers",
        help="Number of concurrent workers to use for performing clones",
        type=int,
        default=multiprocessing.cpu_count(),
    )
    args = parser.parse_args()

    logger.info("reading hgssh JSON document")
    with open(args.input, "r") as f:
        hgssh_data = json.loads(f.read())
        logger.info("JSON document read")

    # Convert the JSON keys to integers
    hgssh_data["offsets"] = {int(k): v for k, v in hgssh_data["offsets"].items()}

    config = Config(filename=args.config)

    consumer_config = {
        # set this so offsets are committed to Zookeeper
        "api_version": (0, 8, 1),
        "bootstrap_servers": [
            host.strip() for host in config.c.get("consumer", "hosts").split(",")
        ],
        "client_id": config.c.get("consumer", "client_id"),
        "enable_auto_commit": False,
        "group_id": config.c.get("consumer", "group"),
        "max_partition_fetch_bytes": MAX_BUFFER_SIZE,
        "value_deserializer": value_deserializer,
    }

    topic = config.c.get("consumer", "topic")

    topicpartitions = [
        TopicPartition(topic, partition)
        for partition, (start_offset, end_offset) in sorted(
            hgssh_data["offsets"].items()
        )
        # there is no need to do an assignment if the length of the
        # bootstrap message range is 0
        if start_offset != end_offset
    ]

    consumer = KafkaConsumer(**consumer_config)

    # This call populates topic metadata for all topics in the cluster.
    consumer.topics()

    outputdata = collections.defaultdict(list)

    # We will remove repos from this set as we replicate them
    # Once this is an empty set we are done
    repositories_to_clone = set()
    for repo in hgssh_data["repositories"]:
        filterresult = config.filter(repo)

        if filterresult.passes_filter:
            repositories_to_clone.add(repo)
        else:
            outputdata[repo].append("filtered by rule %s" % filterresult.rule)

    extra_messages = collections.defaultdict(
        collections.deque
    )  # maps repo names to extra processing messages
    clone_futures_repo_mapping = {}  # maps cloning futures to repo names
    extra_messages_futures_repo_mapping = (
        {}
    )  # maps extra messages futures to repo names

    # Overwrite default hglib path so handle_message_main and it's derivatives
    # use the correct virtualenv
    hglib.HGPATH = config.c.get("programs", "hg")

    # Maps partitions to the list of messages within the bootstrap range
    aggregate_messages_by_topicpartition = {tp.partition: [] for tp in topicpartitions}

    # Gather all the Kafka messages within the bootstrap range for each partition
    for topicpartition in topicpartitions:
        start_offset, end_offset = hgssh_data["offsets"][topicpartition.partition]

        end_offset -= 1

        # Assign the consumer to the next partition and move to the start offset
        logger.info("assigning the consumer to partition %s" % topicpartition.partition)
        consumer.assign([topicpartition])

        logger.info("seeking the consumer to offset %s" % start_offset)
        consumer.seek(topicpartition, start_offset)
        consumer.commit(offsets={topicpartition: OffsetAndMetadata(start_offset, "")})

        logger.info(
            "partition %s of topic %s moved to offset %s"
            % (topicpartition.partition, topicpartition.topic, start_offset)
        )

        # Get all the messages we need to process from kafka
        for message in consumer:
            # Check if the message we are processing is within the range of accepted messages
            # If we are in the range, add this message to the list of messages on this partition
            # If we are at the end of the range, break from the loop and move on to the next partition
            if message.offset <= end_offset:
                aggregate_messages_by_topicpartition[message.partition].append(message)
                logger.info(
                    "message on partition %s, offset %s has been collected"
                    % (message.partition, message.offset)
                )

            consumer.commit(
                offsets={
                    TopicPartition(topic, message.partition): OffsetAndMetadata(
                        message.offset + 1, ""
                    ),
                }
            )

            if message.offset >= end_offset:
                logger.info(
                    "finished retrieving messages on partition %s" % message.partition
                )
                break

    logger.info("finished retrieving messages from Kafka")

    # Process the previously collected messages
    with futures.ThreadPoolExecutor(args.workers) as e:
        for partition, messages in sorted(aggregate_messages_by_topicpartition.items()):
            logger.info("processing messages for partition %s" % partition)
            for message in messages:
                payload = message.value

                # Ignore heartbeat messages
                if payload["name"] == "heartbeat-1":
                    continue

                if payload["path"] in repositories_to_clone:
                    # If we have not yet replicated the repository for this message,
                    # of the repo sync message is not tagged with the bootstrap flag,
                    # move on to the next message. The assumed upcoming hg-repo-sync-2
                    # message will clone the data represented in this message anyways.
                    if payload["name"] != "hg-repo-sync-2" or not payload["bootstrap"]:
                        continue

                    logger.info("scheduled clone for %s" % payload["path"])

                    # Schedule the repo sync
                    clone_future = e.submit(
                        clone_repo,
                        config,
                        payload["path"],
                        payload["requirements"],
                        payload["hgrc"],
                        payload["heads"],
                    )

                    # Here we register the future against its repo name
                    clone_futures_repo_mapping[clone_future] = payload["path"]

                    # Remove the repo from the set of repos
                    # which have not been scheduled to sync
                    repositories_to_clone.remove(payload["path"])
                elif payload["path"] not in outputdata:
                    # If the repo is not in the list of repositories to clone,
                    # and the repo is not in the outputdata object (ie hasn't
                    # errored out, by being filtered or otherwise),
                    # then we have already scheduled the repo sync and we will
                    # need to process this message once the sync completes.
                    extra_messages[payload["path"]].append((config, payload))
                    logger.info(
                        "extra messages found for %s: %s total"
                        % (payload["path"], len(extra_messages[payload["path"]]))
                    )

        if repositories_to_clone:
            logger.error(
                "did not receive expected sync messages for %s" % repositories_to_clone
            )

            # Add errors to audit output
            for repo in repositories_to_clone:
                outputdata[repo].append("did not receive sync message")

        # Process clones
        remaining_clones = len(clone_futures_repo_mapping)
        for completed_future in futures.as_completed(clone_futures_repo_mapping):
            repo = clone_futures_repo_mapping[completed_future]

            exc = completed_future.exception()
            if exc:
                message = "error triggering replication of Mercurial repo %s: %s" % (
                    repo,
                    str(exc),
                )
                logger.error(message)

                # Add error to audit output
                outputdata[repo].append(message)
            else:
                logger.info("%s successfully cloned" % repo)

            remaining_clones -= 1

            logger.info("%s repositories remaining" % remaining_clones)

            # Schedule extra message processing if necessary
            if repo in extra_messages:
                logger.info("scheduling extra processing for %s" % repo)
                future = e.submit(seqmap, handle_message_main, extra_messages[repo])
                extra_messages_futures_repo_mapping[future] = repo

        # Process extra messages
        total_message_batches = len(extra_messages_futures_repo_mapping)
        for completed_future in futures.as_completed(
            extra_messages_futures_repo_mapping
        ):
            repo = extra_messages_futures_repo_mapping[completed_future]

            exc = completed_future.exception()
            if exc:
                message = "error processing extra messages for %s: %s" % (
                    repo,
                    str(exc),
                )
                logger.error(message)

                # Add error to audit output
                outputdata[repo].append(message)
            else:
                logger.info("extra processing for %s completed successfully" % repo)

            total_message_batches -= 1
            logger.info("%s batches remaining" % total_message_batches)

    logger.info("%s bootstrap process complete" % config.c.get("consumer", "group"))

    # If anything broke, dump the errors and set exit code 1
    if outputdata:
        with open("/repo/hg/hgweb_bootstrap_out.json", "w") as f:
            f.write(json.dumps(outputdata))
        return 1
