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
        tree = None
        rev = None
        autoland = False
        comments = None
        for prop in payload['build']['properties']:
            if prop[0] == 'revision':
                rev = prop[1]
            elif prop[0] == 'branch':
                tree = prop[1]
        try:
            for change in payload['build']['sourceStamp']['changes']:
                comments = change['comments']
                if '--autoland' in comments:
                    autoland = True
        except KeyError:
            pass

        #if tree == 'try':
        #    print(rev, autoland, comments)
        if autoland:
            logger.debug('found autoland job: %s %s' % (tree, rev))

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
            pushlog = mercurial.get_pushlog(tree, rev)
            if not pushlog:
                logger.error('could not retrieve pushlog')
                return

            changesets = mercurial.get_changesets(tree, pushlog)
            if not changesets:
                logger.error('could not retrieve changesets')
                return

            bugid = None
            for changeset in changesets:
                bugid = bugid or extract_bugid(changesets[changeset])

            if not bugid:
                logger.error('could not find bug id')
                return

            # insert into database
            query = """
                insert into AutolandRequest(tree,revision,bugid,last_updated)
                values(%s,%s,%s,%s)
            """
            cursor.execute(query, (tree, rev, bugid, datetime.datetime.now()))
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
            logger.error('pulse error: ' + str(e))

if __name__ == '__main__':
    main()
