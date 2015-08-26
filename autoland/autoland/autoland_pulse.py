#!/usr/bin/env python
import argparse
import amqp
import datetime
import json
import logging
import platform
import psycopg2
import time

from mozillapulse import consumers

from mozlog.structured import commandline

import config

# Some global variables that we need in the 'handle_message' callback
auth = None
dbconn = None
logger = None


def read_credentials():
    return config.get('pulse')['user'], config.get('pulse')['passwd']


def handle_message(data, message):
    message.ack()


def main():
    global auth
    global dbconn
    global logger

    parser = argparse.ArgumentParser()
    dsn = 'dbname=autoland user=autoland host=localhost password=autoland'
    parser.add_argument('--dsn', default=dsn,
                        help='Postgresql DSN connection string')
    parser.add_argument('--message-log-path', default=None,
                        help='Path to which to log received messages')
    commandline.add_logging_group(parser)
    args = parser.parse_args()

    logging.basicConfig()
    logger = commandline.setup_logging('autoland-pulse', vars(args), {})
    logger.info('starting pulse listener')

    while not dbconn:
        try:
            dbconn = psycopg2.connect(args.dsn)
        except psycopg2.OperationalError:
            time.sleep(0.1)

    user, password = read_credentials()

    unique_label = 'autoland-%s' % platform.node()
    pulse = consumers.BuildConsumer(applabel=unique_label, user=user,
                                    password=password)
    pulse.configure(topic=['build.#.finished'], callback=handle_message)
    logger.debug('applabel: %s' % unique_label)
    while True:
        try:
            pulse.listen()
        except amqp.exceptions.ConnectionForced as e:
            logger.error('pulse error: ' + str(e))
        except IOError as e:
            logger.error('pulse error: ' + str(e))


if __name__ == '__main__':
    main()
