#!/usr/bin/env python
import argparse
import amqp
import datetime
import httplib
import json
import logging
import psycopg2
import re
import string
import uuid

seen_comments = {}

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

def extract_bugid(patch):
    #TODO: check to see if there is an "official" re for this
    bugid = re.compile('[Bb]ug (\d+)')
    m = re.search(bugid, patch)
    if m:
        return m.groups()[0]

def is_known_autoland_job(dbconn, tree, rev): 
    cursor = dbconn.cursor()

    # see if we know already know about this autoland request
    query = """select revision from AutolandRequest
               where tree=%(tree)s
               and substring(revision, 0, %(len)s)=%(rev)s"""
    cursor.execute(query, {'tree': tree,
                           'len': len(rev) + 1,
                           'rev': rev})
    row = cursor.fetchone()
    return row is not None

def handle_message(data, message):
    message.ack()

    key = data['_meta']['routing_key']
    payload = data['payload']

    if message_log_path:
        with open(message_log_path, 'a') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    if key.find('started') != -1:
        blame = payload['build']['blame']

        tree = None
        rev = None
        autoland = False
        message = None
        bugid = None
        for prop in payload['build']['properties']:
            if prop[0] == 'revision':
                rev = prop[1]
            elif prop[0] == 'branch':
                tree = prop[1]
        try:
            for change in payload['build']['sourceStamp']['changes']:
                comments = change['comments']
                index = comments.find('--autoland')
                if index > -1:
                    autoland = True
                    message = comments[index + len('--autoland') + 1:].strip()
                    bugid = extract_bugid(message)
        except KeyError:
            pass

        if autoland:
            logger.info('found autoland job: %s %s' % (tree, rev))

            if not bugid:
                logger.info('autoland job missing bugid')
                return
            else:
                logger.info('bugid %s' % bugid)

            if is_known_autoland_job(dbconn, tree, rev):
                return

            logger.info('found new autoland job')

            # insert into database
            query = """
                insert into AutolandRequest(tree,revision,bugid,blame,message,last_updated)
                values(%s,%s,%s,%s,%s,%s)
            """
            cursor = dbconn.cursor()
            cursor.execute(query, (tree, rev, bugid, blame, message, datetime.datetime.now()))
            dbconn.commit()
    elif key.find('finished') != -1:
        rev = None
        tree = None
        for prop in payload['build']['properties']:
            if prop[0] == 'revision':
                rev = prop[1]
            elif prop[0] == 'branch':
                tree = prop[1]

        if tree and rev:
            if is_known_autoland_job(dbconn, tree, rev):
                logger.info('updating autoland job: %s %s' % (tree, rev))

                pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)
                logger.info('pending: %d running: %d builds: %d' % (len(pending), len(running), len(builds)))

                query = """
                    update AutolandRequest set pending=%s,
                        running=%s,builds=%s,last_updated=%s
                    where tree=%s
                    and substring(revision, 0, %s)=%s"""
                cursor = dbconn.cursor()
                cursor.execute(query, (len(pending), len(running), len(builds), datetime.datetime.now(), tree, len(rev) + 1, rev))
                dbconn.commit()

def main():
    global auth
    global dbconn
    global logger
    global message_log_path

    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default='dbname=autoland user=autoland host=localhost password=autoland',
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

    unique_label = 'autoland-%s' % uuid.uuid4()
    pulse = consumers.BuildConsumer(applabel=unique_label)
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
