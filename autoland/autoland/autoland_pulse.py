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
    bugid = re.compile('[Bb]ug (\d+)')
    m = re.search(bugid, patch)
    if m:
        return m.groups()[0]

def handle_message(data, message):
    message.ack()

    key = data['_meta']['routing_key']
    payload = data['payload']

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

        #if tree == 'try':
        #    print(json.dumps(payload, sort_keys=True, indent=2))
        #    print(rev, autoland, comments)
        if autoland:
            logger.debug('found autoland job: %s %s' % (tree, rev))

            if not bugid:
                logger.debug('autoland job missing bugid')
                return
            else:
                logger.debug('bugid %s' % bugid)


            cursor = dbconn.cursor()

            # see if we know already know about this autoland request
            query = """select revision from AutolandRequest
                       where tree=%(tree)s
                       and substring(revision, 0, %(len)s)=%(rev)s"""
            cursor = dbconn.cursor()
            cursor.execute(query, {'tree': tree,
                                   'len': len(rev) + 1,
                                   'rev': rev})
            row = cursor.fetchone()
            if row is not None:
                logger.debug('autoland job already known')
                return

            logger.debug('found new autoland job!')

            # insert into database
            query = """
                insert into AutolandRequest(tree,revision,bugid,blame,message,last_updated)
                values(%s,%s,%s,%s,%s,%s)
            """
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

        if tree == 'try' and rev:
            #print('finished', tree, rev)
            query = """select revision from AutolandRequest
                       where tree=%(tree)s
                       and substring(revision, 0, %(len)s)=%(rev)s"""
            cursor = dbconn.cursor()
            cursor.execute(query, {'tree': tree,
                                   'len': len(rev) + 1,
                                   'rev': rev})
            row = cursor.fetchone()
            if row is not None:
                logger.debug('updating autoland job: %s %s' % (tree, rev))
                pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)
                logger.debug('pending: %d running: %d builds: %d' % (len(pending), len(running), len(builds)))

                query = """
                    update AutolandRequest set pending=%s,
                        running=%s,builds=%s,last_updated=%s
                    where tree=%s
                    and substring(revision, 0, %s)=%s"""
                cursor.execute(query, (len(pending), len(running), len(builds), datetime.datetime.now(), tree, len(rev) + 1, rev))

            dbconn.commit()

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
    pulse = consumers.BuildConsumer(applabel=unique_label)
    pulse.configure(topic=['build.#'], callback=handle_message)
    while True:
        try:
            pulse.listen()
        except IOError as e:
            logger.debug('pulse error: ' + str(e))

if __name__ == '__main__':
    main()
