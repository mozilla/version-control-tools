# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This file contains Nagios checks that are specific to vcsreplicator.

from __future__ import absolute_import, unicode_literals

import argparse
import sys

from .config import Config
from .consumer import consumer_offsets_and_lag


def check_consumer_lag():
    parser = argparse.ArgumentParser()
    parser.add_argument('config',
            help='Path to config file to load')
    parser.add_argument('--warning-lag-count', default=5, type=int,
            help='Number of messages behind after which a warning will be '
                 'issued')
    parser.add_argument('--warning-lag-time', default=30.0, type=float,
            help='Time behind after which a warning will be issued')
    parser.add_argument('--critical-lag-count', default=10, type=int,
            help='Number of messages behind after which an error will be '
                 'issued')
    parser.add_argument('--critical-lag-time', default=60.0, type=float,
            help='Time behind after which an error will be issued')

    args = parser.parse_args()

    config = Config(filename=args.config)
    client = config.get_client_from_section('consumer', timeout=5)
    topic = config.c.get('consumer', 'topic')
    group = config.c.get('consumer', 'group')

    offsets = consumer_offsets_and_lag(client, topic, [group])[group]

    exit = 0
    good = 0
    bad = 0
    output = []

    for partition, (offset, available, lag_time) in sorted(offsets.items()):
        # Consumer is fully caught up.
        if offset >= available:
            good += 1
            output.append('OK - partition %d is completely in sync (%d/%d)' % (
                partition, offset, available))
            continue

        bad += 1
        lag = available - offset
        if lag >= args.critical_lag_count:
            exit = 2
            label = 'CRITICAL'
        elif lag >= args.warning_lag_count:
            exit = max(exit, 1)
            label = 'WARNING'
        else:
            label = 'OK'

        output.append('%s - partition %d is %d messages behind (%d/%d)' % (
            label, partition, lag, offset, available))

        if lag_time >= args.critical_lag_time:
            exit = 2
            label = 'CRITICAL'
        elif lag_time >= args.warning_lag_time:
            exit = max(exit, 1)
            label = 'WARNING'
        else:
            label = 'OK'

        output.append('%s - partition %d is %0.3f seconds behind' % (
            label, partition, lag_time))

    if exit == 2:
        print('CRITICAL - %d/%d partitions out of sync' % (bad, len(offsets)))
    elif exit:
        print('WARNING - %d/%d partitions out of sync' % (bad, len(offsets)))
    elif good == len(offsets):
        print('OK - %d/%d consumers completely in sync' % (good, len(offsets)))
    else:
        drifted = len(offsets) - good
        print('OK - %d/%d consumers out of sync but within tolerances' % (
            drifted, len(offsets)))

    print('')
    for m in output:
        print(m)

    print('')
    print('See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html')
    print('for details about this check.')

    sys.exit(exit)
