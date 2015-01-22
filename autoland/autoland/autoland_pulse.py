#!/usr/bin/env python
import argparse
import amqp
import datetime
import httplib
import json
import logging
import platform
import psycopg2
import re
import string

from mozillapulse import consumers

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)

import selfserve

# Some global variables that we need in the 'handle_message' callback
auth = None
dbconn = None
logger = None
message_log_path = None

REV_LENGTH = 12


def read_credentials():
    with open('config.json') as f:
        pulse = json.load(f)['pulse']
        return pulse['user'], pulse['passwd']


def is_known_testrun(dbconn, tree, rev):
    cursor = dbconn.cursor()

    query = """select revision from Testrun
               where tree=%(tree)s
               and substring(revision, 0, %(len)s)=%(rev)s"""
    cursor.execute(query, {'tree': tree,
                           'len': REV_LENGTH + 1,
                           'rev': rev[:REV_LENGTH]})

    row = cursor.fetchone()
    return row is not None


def extract_tree_and_rev(payload):
    tree = None
    rev = None
    for prop in payload['build']['properties']:
        if prop[0] == 'revision':
            rev = prop[1]
        elif prop[0] == 'branch':
            tree = prop[1]

    return tree, rev


def handle_message(data, message):
    message.ack()

    key = data['_meta']['routing_key']
    payload = data['payload']

    if message_log_path:
        with open(message_log_path, 'a') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    tree, rev = extract_tree_and_rev(payload)

    if tree and rev and is_known_testrun(dbconn, tree, rev):
        logger.info('updating testrun: %s %s' % (tree, rev))

        pending, running, builds = selfserve.jobs_for_revision(auth,
                                                               tree,
                                                               rev)

        npending = len(pending)
        nrunning = len(running)
        nbuilds = len(builds)
        logger.info('pending: %d running: %d builds: %d' %
                    (npending, nrunning, nbuilds))

        query = """
            update Testrun set pending=%s,
                running=%s,builds=%s,last_updated=%s
            where tree=%s
            and substring(revision, 0, %s)=%s"""
        cursor = dbconn.cursor()
        cursor.execute(query, (npending, nrunning, nbuilds,
                       datetime.datetime.now(), tree,
                       REV_LENGTH + 1, rev[:REV_LENGTH]))
        dbconn.commit()


def main():
    global auth
    global dbconn
    global logger
    global message_log_path

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

    auth = selfserve.read_credentials()
    dbconn = psycopg2.connect(args.dsn)

    if args.message_log_path:
        try:
            open(args.message_log_path, 'w')
            message_log_path = args.message_log_path
        except IOError:
            pass

    user, password = read_credentials()

    unique_label = 'autoland-%s' % platform.node()
    pulse = consumers.BuildConsumer(applabel=unique_label, user=user,
                                    password=password)
    pulse.configure(topic=['build.#.started', 'build.#.finished'],
                    callback=handle_message)
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
