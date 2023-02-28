# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This file contains Nagios checks that are specific to vcsreplicator.

from __future__ import absolute_import, unicode_literals

import argparse
import json
import sys

from .aggregator import (
    read_consumer_groups,
    get_aggregation_counts,
)
from .config import (
    Config,
)
from .consumer import (
    consumer_offsets_and_lag,
)


def create_consumer_telegraf_json(offsets):
    """Format the output of `consumer_offsets_and_lag` for consumption
    by the Telegraf `exec` plugin
    """
    return [
        {
            "partition": partition,
            "offset": offset,
            "available": available,
            "lag_time": lag_time,
        }
        for partition, (offset, available, lag_time) in offsets.items()
    ]


def create_aggregator_telegraf_json(consumed, acked):
    """Format the output of `get_aggregation_counts` for consumption
    by the Telegraf `exec` plugin
    """
    partitions = consumed.keys()
    return [
        {
            "partition": partition,
            "consumed_offset": consumed[partition],
            "acked_offset": acked[partition],
        }
        for partition in partitions
    ]


def check_consumer_lag():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config file to load")
    parser.add_argument(
        "--consumer-section",
        default="consumer",
        help="Config section Kafka config should be read from",
    )
    parser.add_argument(
        "--warning-lag-count",
        default=150,
        type=int,
        help="Number of messages behind after which a warning will be " "issued",
    )
    parser.add_argument(
        "--warning-lag-time",
        default=150.0,
        type=float,
        help="Time behind after which a warning will be issued",
    )
    parser.add_argument(
        "--critical-lag-count",
        default=600,
        type=int,
        help="Number of messages behind after which an error will be " "issued",
    )
    parser.add_argument(
        "--critical-lag-time",
        default=600.0,
        type=float,
        help="Time behind after which an error will be issued",
    )
    parser.add_argument(
        "--telegraf",
        action="store_true",
        help="Output data for consumption by Telegraf",
    )

    args = parser.parse_args()

    consumer_section = args.consumer_section

    config = Config(filename=args.config)
    client = config.get_client_from_section(consumer_section, timeout=5)
    topic = config.get(consumer_section, "topic")
    group = config.get(consumer_section, "group")

    try:
        offsets = consumer_offsets_and_lag(client, topic, [group])[group]
    except Exception as e:
        print("WARNING - exception fetching offsets: %s" % e)
        print("")
        raise

    if args.telegraf:
        telegraf_data = create_consumer_telegraf_json(offsets)
        print(json.dumps(telegraf_data, sort_keys=True))
        sys.exit(0)

    exitcode = 0
    good = 0
    bad = 0
    output = []
    drift_warned = False

    for partition, (offset, available, lag_time) in sorted(offsets.items()):
        # Consumer is fully caught up.
        if offset >= available:
            good += 1
            output.append(
                "OK - partition %d is completely in sync (%d/%d)"
                % (partition, offset, available)
            )
            continue

        bad += 1
        lag = available - offset
        if lag >= args.critical_lag_count:
            exitcode = 2
            label = "CRITICAL"
        elif lag >= args.warning_lag_count:
            exitcode = max(exitcode, 1)
            label = "WARNING"
        else:
            label = "OK"

        output.append(
            "%s - partition %d is %d messages behind (%d/%d)"
            % (label, partition, lag, offset, available)
        )

        if lag_time is None:
            output.append(
                "WARNING - could not determine lag time for " "partition %d" % partition
            )
            # TODO raise warning for inability to determine lag time if persistent.
            # exitcode = max(exitcode, 1)
        else:
            if lag_time >= args.critical_lag_time:
                exitcode = 2
                label = "CRITICAL"
            elif lag_time >= args.warning_lag_time:
                exitcode = max(exitcode, 1)
                label = "WARNING"
            else:
                label = "OK"

            output.append(
                "%s - partition %d is %0.3f seconds behind"
                % (label, partition, lag_time)
            )

            # Clock drift between producer and consumer.
            if lag_time < 0.0 and not drift_warned:
                exitcode = max(exitcode, 1)
                output.append(
                    "WARNING - clock drift of %.3f seconds between "
                    "producer and consumer; check NTP sync" % lag_time
                )
                drift_warned = True

    if exitcode == 2:
        print("CRITICAL - %d/%d partitions out of sync" % (bad, len(offsets)))
    elif exitcode:
        print("WARNING - %d/%d partitions out of sync" % (bad, len(offsets)))
    elif good == len(offsets):
        print("OK - %d/%d consumers completely in sync" % (good, len(offsets)))
    else:
        drifted = len(offsets) - good
        print(
            "OK - %d/%d consumers out of sync but within tolerances"
            % (drifted, len(offsets))
        )

    print("")
    for m in output:
        print(m)

    print("")
    print(
        "See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html"
    )
    print("for details about this check.")

    sys.exit(exitcode)


def check_aggregator_lag():
    """Check the lag of an aggregator daemon."""
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path to config file to load")
    parser.add_argument(
        "--warning-count",
        default=40,
        type=int,
        help="Total number of messages behind after which a " "warning will be issued",
    )
    parser.add_argument(
        "--critical-count",
        default=100,
        type=int,
        help="Total number of messages behind after which a "
        "critical will be reported",
    )
    parser.add_argument(
        "--telegraf",
        action="store_true",
        help="Output data for consumption by Telegraf",
    )

    args = parser.parse_args()

    config = Config(filename=args.config)
    client = config.get_client_from_section("aggregator", timeout=5)
    monitor_topic = config.get("aggregator", "monitor_topic")
    groups_path = config.get("aggregator", "monitor_groups_file")
    ack_group = config.get("aggregator", "ack_group")

    try:
        groups = read_consumer_groups(groups_path)
        consumed, acked, counts = get_aggregation_counts(
            client, monitor_topic, groups, ack_group
        )
    except Exception as e:
        print("WARNING - exception fetching data: %s" % e)
        print("")
        raise

    if args.telegraf:
        telegraf_data = create_aggregator_telegraf_json(consumed, acked)
        print(json.dumps(telegraf_data, sort_keys=True))
        sys.exit(0)

    message_count = sum(counts.values())

    output = []

    if not message_count:
        exit_code = 0
        output.append("OK - aggregator has copied all fully replicated messages")
    else:
        if message_count >= args.critical_count:
            exit_code = 2
            label = "CRITICAL"
        elif message_count >= args.warning_count:
            exit_code = 1
            label = "WARNING"
        else:
            exit_code = 0
            label = "OK"

        output.append(
            "%s - %d messages from %d partitions behind"
            % (label, message_count, len(counts))
        )

    output.append("")
    for partition in sorted(consumed.keys()):
        consume_offset = consumed[partition]
        acked_offset = acked[partition]
        unacked = consume_offset - acked_offset
        if unacked <= 0:
            label = "OK"
        elif unacked >= args.critical_count:
            label = "CRITICAL"
        elif unacked >= args.warning_count:
            label = "WARNING"

        if unacked <= 0:
            output.append(
                "%s - partition %d is completely in sync (%d/%d)"
                % (label, partition, acked_offset, consume_offset)
            )
        else:
            output.append(
                "%s - partition %d is %d messages behind (%d/%d)"
                % (label, partition, unacked, acked_offset, consume_offset)
            )

    for l in output:
        print(l)

    print("")
    print(
        "See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html"
    )
    print("for details about this check.")

    sys.exit(exit_code)
