#!/usr/bin/env python
import argparse
import datetime
import httplib
import json
import logging
import psycopg2
import re
import requests
import string
import uuid

from mozillapulse import consumers

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)

import mercurial
import selfserve

dbconn = None
logger = None

def extract_try(patch):
    for line in patch.split('\n'):
        i = line.find('try:')
        if i != -1:
            return line[i:]

def extract_bugid(patch):
    #TODO: check to see if there is an "official" re for this
    bugid = re.compile('[Bb]ug (\d+) ')
    m = re.search(bugid, patch)
    if m:
        return m.groups()[0]

def handle_message(data, message):
    message.ack()

    payload = data['payload']

    if not 'tree' in payload:
        return

    tree = payload['tree']

    if tree != 'try':
        #logger.error('received update for tree other than try: %s' % tree)
        return

    rev = payload['revision']
    #key = data['_meta']['routing_key']
    #print(rev, key)

    patch = mercurial.get_raw_revision(tree, rev)
    if patch:
        try_string = extract_try(patch)

        if '--autoland' in try_string:
            logger.debug('found autoland job: %s %s: %s' % (tree, rev, try_string))

            bugid = extract_bugid(patch)
            if not bugid:
                logger.error('could not find bug id for autoland request')
                return

            pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)
            logger.debug('pending: %d running: %d builds: %d' % (len(pending), len(running), len(builds)))

            query = """select revision from AutolandRequest
                       where tree=%(tree)s and revision=%(rev)s"""

            cursor = dbconn.cursor()
            cursor.execute(query, {'tree': tree, 'rev': rev})
            row = cursor.fetchone()
            if row is None:
                query = """
                    insert into AutolandRequest(tree,revision,bugid,patch,pending,
                        running,builds,last_updated)
                    values(%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cursor.execute(query, (tree, rev, bugid, patch,
                                       len(pending), len(running),
                                       len(builds), datetime.datetime.now()))
            else:
                query = """
                    update AutolandRequest set pending=%s,
                        running=%s,builds=%s,last_updated=%s
                    where tree=%s and revision=%s
                """
                cursor.execute(query, (len(pending), len(running), len(builds), datetime.datetime.now(), tree, rev))

            dbconn.commit()
    else:
        logger.debug('could not find revision %s on %s' % (rev, tree))

def main():
    global auth
    global dbconn
    global logger

    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default='dbname=autoland user=autoland host=localhost password=autoland',
                        help='Postgresql DSN connection string')
    commandline.add_logging_group(parser)
    args = parser.parse_args()

    logging.basicConfig()
    logger = commandline.setup_logging('autoland-pulse', vars(args), {})
    logger.debug('starting pulse listener')

    auth = selfserve.read_credentials()
    dbconn = psycopg2.connect(args.dsn)

    unique_label = 'autoland-%s' % uuid.uuid4()
    pulse = consumers.NormalizedBuildConsumer(applabel=unique_label)
    pulse.configure(topic=['build.try.#', 'unittest.try.#'], callback=handle_message)
    while True:
        try:
            pulse.listen()
        except IOError as e:
            logger.error('pulse error: ' + str(e))

if __name__ == '__main__':
    main()
