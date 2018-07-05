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
    process_message,
    MAX_BUFFER_SIZE,
)


REPOS_DIR = '/repo/hg/mozilla'

logger = logging.getLogger('vcsreplicator.bootstrap')

# Quiet down the vcsreplicator.consumer logger when these scripts are running
consumer_logger = logging.getLogger('vcsreplicator.consumer')
null_handler = logging.FileHandler('/dev/null')
consumer_logger.addHandler(null_handler)


def clone_repo(config, path, requirements, hgrc, heads, create=False):
    """Wraps process_hg_sync to provide logging"""
    logger.info('syncing repo: %s' % path)
    try:
        return process_hg_sync(config, path, requirements, hgrc, heads, create=False)
    finally:
        logger.info('exiting sync for: %s' % path)


def hgssh():
    '''hgssh component of the vcsreplicator bootstrap procedure.'''
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config file')
    parser.add_argument('hg', help='Path to hg executable for use in bootstrap process')
    parser.add_argument('workers', help='Number of concurrent workers to use for publishing messages', type=int,
                        default=multiprocessing.cpu_count())
    args = parser.parse_args()

    config = Config(filename=args.config)

    topic = config.c.get('replicationproducer', 'topic')

    # Create consumer to gather partition offsets
    consumer_config = {
        # set this so offsets are committed to Zookeeper
        'api_version': (0, 8, 1),
        'bootstrap_servers': config.c.get('replicationproducer', 'hosts'),
        'enable_auto_commit': False,  # We don't actually commit but this is just for good measure
    }
    consumer = KafkaConsumer(**consumer_config)

    partitions = consumer.partitions_for_topic(topic)

    # Gather the initial offsets
    topicpartitions = [
        TopicPartition(topic, partition_number)
        for partition_number in partitions
    ]
    offsets_start = consumer.end_offsets(topicpartitions)
    logger.info('gathered initial Kafka offsets')

    # Mapping of `replicatesync` future to corresponding repo name
    replicatesync_futures = {}
    with futures.ThreadPoolExecutor(args.workers) as e:
        # Create a future which makes a `replicatesync` call
        # for each repo on hg.mo
        for repo in find_hg_repos(REPOS_DIR):
            # Create a future to call `replicatesync` for this repo
            replicatesync_args = [
                args.hg,
                '-R', repo,
                'replicatesync',
                '--bootstrap',
            ]
            replicatesync_futures.update({
                e.submit(subprocess.check_output, replicatesync_args): repo
            })

            logger.info('calling `replicatesync --bootstrap` on %s' % repo)

        # Execute the futures and raise an Exception on fail
        for future in futures.as_completed(replicatesync_futures):
            repo = replicatesync_futures[future]

            exc = future.exception()
            if exc:
                logger.error('error occurred calling `replicatesync --bootstrap` on %s: %s' % (repo, exc))
                raise Exception('error triggering replication of Mercurial repo %s: %s' %
                                (repo, exc))
            logger.info('called `replicatesync --bootstrap` on %s successfully' % repo)

    # Gather the final offsets
    offsets_end = consumer.end_offsets(topicpartitions)
    logger.info('gathered final Kafka offsets')

    # Create map of partition numbers to (start, end) offset tuples
    offsets_combined = {
        int(topicpartition.partition): (offsets_start[topicpartition], offsets_end[topicpartition])
        for topicpartition in topicpartitions
    }

    # Create JSON for processing in ansible and print to stdout
    # Convert repo paths into their wire representations
    output = {
        'offsets': offsets_combined,
        'repositories': sorted([
            config.get_replication_path_rewrite(repo)
            for repo in replicatesync_futures.values()
        ]),
    }

    print(json.dumps(output))
    logger.info('hgssh bootstrap process complete')


def hgweb():
    '''hgweb component of the vcsreplicator bootstrap procedure. Takes a
    vcsreplicator config path on the CLI and takes a JSON data structure
    on stdin'''
    import argparse

    # Configure logging
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s %(message)s')
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path of config file to load')
    parser.add_argument('hg', help='Path to hg executable for use in bootstrap process')
    parser.add_argument('input', help='JSON data input (output from the hgssh bootstrap procedure) file path')
    parser.add_argument('workers', help='Number of concurrent workers to use for performing clones', type=int,
                        default=multiprocessing.cpu_count())
    args = parser.parse_args()

    logger.info('reading hgssh JSON document')
    with open(args.input, 'r') as f:
        hgssh_data = json.loads(f.read())
        logger.info('JSON document read')

    # Convert the JSON keys to integers
    hgssh_data['offsets'] = {
        int(k): v
        for k, v in hgssh_data['offsets'].items()
    }

    config = Config(filename=args.config)

    consumer_config = {
        # set this so offsets are committed to Zookeeper
        'api_version': (0, 8, 1),
        'bootstrap_servers': config.c.get('consumer', 'hosts'),
        'client_id': config.c.get('consumer', 'client_id'),
        'enable_auto_commit': False,
        'group_id': config.c.get('consumer', 'group'),
        'max_partition_fetch_bytes': MAX_BUFFER_SIZE,
        'value_deserializer': value_deserializer,
    }

    topic = config.c.get('consumer', 'topic')

    topicpartitions = [
        TopicPartition(topic, partition)
        for partition in hgssh_data['offsets']
    ]

    consumer = KafkaConsumer(**consumer_config)
    consumer.assign(topicpartitions)
    logger.info('Kafka consumer assigned to replication topic')

    # Seek all partitions to their start offsets and commit
    for i, (start, end) in hgssh_data['offsets'].items():
        consumer.seek(TopicPartition(topic, i), start)
        logger.info('partition %s of topic %s moved to offset %s' % (i, topic, start))
    consumer.commit()

    # We will remove repos from this set as we replicate them
    # Once this is an empty set we are done
    repositories_to_clone = set(hgssh_data['repositories'])

    extra_messages = collections.defaultdict(collections.deque)  # maps repo names to extra processing messages
    clone_futures_repo_mapping = {}  # maps cloning futures to repo names
    extra_messages_futures_repo_mapping = {}  # maps extra messages futures to repo names

    # Overwrite default hglib path so process_message and it's derivatives
    # use the correct virtualenv
    hglib.HGPATH = args.hg

    # Maps partitions to the list of messages within the bootstrap range
    aggregate_messages_by_topicpartition = {
        tp.partition: []
        for tp in topicpartitions
    }

    # Maps a partition to a boolean indicating if there are more messages to process
    # for this partition. When all the values in this mapping are True, the message
    # collection step is complete
    completed_aggregates = {
        partition: False
        for partition, (start, end) in hgssh_data['offsets'].items()
        # We don't need to wait for completion if a partition's
        # start/end offset are the same
        if start != end
    }

    # Get all the messages we need to process from kafka
    for message in consumer:
        end_offset_for_partition = hgssh_data['offsets'][message.partition][1] - 1

        # Check if the message we are processing is within the range of accepted messages
        # If we are in the range, add this message to the list of messages on this partition
        # If not, mark this partition as complete
        # If the offsets are equal, do both steps
        if message.offset <= end_offset_for_partition:
            aggregate_messages_by_topicpartition[message.partition].append(message)
            logger.info('message on partition %s, offset %s has been collected' % (message.partition, message.offset))

        if message.offset >= end_offset_for_partition:
            completed_aggregates[message.partition] = True
            logger.info('finished retrieving messages on partition %s' % message.partition)

            # Commit and exit the Kafka consume loop if we have gathered all required messages
            if all(completed for completed in completed_aggregates.values()):
                consumer.commit(offsets={
                    TopicPartition(topic, message.partition): OffsetAndMetadata(message.offset + 1, ''),
                })
                break

            # Don't commit this offset if it is outside the bootstrap range
            continue

        consumer.commit(offsets={
            TopicPartition(topic, message.partition): OffsetAndMetadata(message.offset + 1, ''),
        })

    logger.info('finished retrieving messages from Kafka')

    # TODO send details of failures somewhere to audit
    exitcode = 0

    # Process the previously collected messages
    with futures.ThreadPoolExecutor(args.workers) as e:
        for partition, messages in aggregate_messages_by_topicpartition.items():
            logger.info('processing messages for partition %s' % partition)
            for message in messages:
                payload = message.value

                # Ignore heartbeat messages
                if payload['name'] == 'heartbeat-1':
                    continue

                if payload['path'] in repositories_to_clone:
                    # If we have not yet replicated the repository for this message,
                    # of the repo sync message is not tagged with the bootstrap flag,
                    # move on to the next message. The assumed upcoming hg-repo-sync-2
                    # message will clone the data represented in this message anyways.
                    if payload['name'] != 'hg-repo-sync-2' or not payload['bootstrap']:
                        continue

                    # Schedule the repo sync
                    clone_future = e.submit(clone_repo, config, payload['path'],
                                            payload['requirements'], payload['hgrc'],
                                            payload['heads'], create=True)

                    # Here we register the future against its repo name
                    clone_futures_repo_mapping[clone_future] = payload['path']

                    # Remove the repo from the set of repos
                    # which have not been scheduled to sync
                    repositories_to_clone.remove(payload['path'])

                    logger.info('scheduled clone for %s' % payload['path'])
                else:
                    # If the repo is not in the list of repositories to clone,
                    # then we have already scheduled the repo sync and we will
                    # need to process this message once the sync completes.
                    extra_messages[payload['path']].append((config, payload))
                    logger.info('extra messages found for %s: %s total' %
                                (payload['path'], len(extra_messages[payload['path']]))
                    )

        if repositories_to_clone:
            logger.error('did not receive expected sync messages for %s' % repositories_to_clone)
            exitcode = 1

        # Process clones
        remaining_clones = len(clone_futures_repo_mapping)
        for completed_future in futures.as_completed(clone_futures_repo_mapping):
            repo = clone_futures_repo_mapping[completed_future]

            exc = completed_future.exception()
            if exc:
                logger.error('error triggering replication of Mercurial repo %s: %s' %
                            (repo, exc))
                exitcode = 1

            remaining_clones -= 1

            logger.info('%s successfully cloned' % repo)
            logger.info('%s repositories remaining' % remaining_clones)

            # Schedule extra message processing if necessary
            if repo in extra_messages:
                logger.info('scheduling extra processing for %s' % repo)
                configs, payloads = zip(*extra_messages[repo])
                future = e.submit(map, process_message, configs, payloads)
                extra_messages_futures_repo_mapping[future] = repo

        # Process extra messages
        total_message_batches = len(extra_messages_futures_repo_mapping)
        for completed_future in futures.as_completed(extra_messages_futures_repo_mapping):
            repo = extra_messages_futures_repo_mapping[completed_future]

            exc = completed_future.exception()
            if exc:
                logger.error('error triggering replication of Mercurial repo %s: %s' %
                                (repo, exc))
                exitcode = 1

            total_message_batches -= 1

            logger.info('extra processing for %s completed successfully' % repo)
            logger.info('%s batches remaining' % total_message_batches)

    logger.info('%s bootstrap process complete' % config.c.get('consumer', 'group'))

    return exitcode
