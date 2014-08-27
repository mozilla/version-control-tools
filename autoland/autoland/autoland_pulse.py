#!/usr/bin/env python
import argparse
import datetime
import httplib
import json
import logging
import psycopg2
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

def handle_message(data, message):
    message.ack()

    payload = data['payload']
    tree = payload['tree']

    if tree == 'try':
        rev = payload['revision']

        patch = mercurial.get_raw_revision(tree, rev)
        if patch:
            try_string = extract_try(patch)
            logger.debug('found job: %s %s: %s' % (tree, rev, try_string))

            if '--autoland' in try_string:
                pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)
                logger.debug('autoland job: pending: %d running: %d builds: %d' % (len(pending), len(running), len(builds)))

                query = """select revision from AutolandRequest
                           where tree=%(tree)s and revision=%(rev)s"""

                cursor = dbconn.cursor()
                cursor.execute(query, {'tree': tree, 'rev': rev})
                row = cursor.fetchone()
                if row is None:
                    query = """
                        insert into AutolandRequest(tree,revision,patch,pending,
                            running,builds,last_updated)
                        values(%s,%s,%s,%s,%s,%s,%s)
                    """
                    cursor.execute(query, (tree, rev, r.text,
                                           len(pending),
                                           len(running),
                                           len(builds),
                                           datetime.datetime.now()))
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
    pulse.configure(topic='build.#', callback=handle_message)
    pulse.listen()

if __name__ == '__main__':
    main()
