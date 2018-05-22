# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import multiprocessing
import subprocess

import concurrent.futures as futures

from hgmolib import find_hg_repos
from kafka import (
    KafkaConsumer,
    TopicPartition,
)

from .config import Config


REPOS_DIR = '/repo/hg/mozilla'

logger = logging.getLogger('vcsreplicator.bootstrap')


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
                'replicatesync'
            ]
            replicatesync_futures.update({
                e.submit(subprocess.check_output, replicatesync_args): repo
            })

            logger.info('calling `replicatesync` on %s' % repo)

        # Execute the futures and raise an Exception on fail
        for future in futures.as_completed(replicatesync_futures):
            repo = replicatesync_futures[future]

            exc = future.exception()
            if exc:
                logger.error('error occurred calling `replicatesync` on %s: %s' % (repo, exc))
                raise Exception('error triggering replication of Mercurial repo %s: %s' %
                                (repo, exc))
            logger.info('called `replicatesync` on %s successfully' % repo)

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
