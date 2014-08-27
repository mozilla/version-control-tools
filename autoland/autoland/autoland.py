#!/usr/bin/env python
import argparse
import datetime
import json
import logging
import psycopg2
import re
import requests
import time

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)

import selfserve

def handle_landing(logger, dbconn, tree, rev):
    logger.debug('autoland request %s %s can be landed' % (tree, rev))
    cursor = dbconn.cursor()
    query = """
        update AutolandRequest set can_be_landed=TRUE,last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()

def handle_failure(logger, auth, dbconn, tree, rev, build_id):
    job_id = selfserve.rebuild_job(auth, tree, build_id)
    if job_id:
        logger.debug('submitted rebuild request %s for autoland job %s %s' % (job_id, tree, rev))
        cursor = dbconn.cursor()
        query = """
            update AutolandRequest set last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
    else:
        logger.debug('could not rebuild %s for autoland job %s %s' % (build_id, tree, rev))

def handle_autoland_request(logger, auth, dbconn, tree, rev):

    logger.debug('looking at autoland request %s %s' % (tree, rev))

    cursor = dbconn.cursor()
    status = selfserve.job_is_done(auth, tree, rev)
    if not status:
        logger.debug('could not get job status for %s %s' % (tree, rev))
        return
  
    if not status['job_complete']:
        logger.debug('autoland request %s %s job not complete' % (tree, rev))
        # update pending so we won't look at this job again 
        # until we get another update over pulse
        query = """
            update AutolandRequest set pending=null,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
        return

    # everything passed, so we can land
    if status['job_passed']:
        return handle_landing(logger, dbconn, tree, rev)

    pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)
    
    if len(pending) > 0 or len(running) > 0:
        logger.debug('autoland request %s %s still has pending or running jobs: %d %d' % (tree, rev, len(pending), len(running)))
        query = """
            update AutolandRequest set pending=%s,running=%s,
                                       builds=%s,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (len(pending), len(running), len(builds), datetime.datetime.now(), tree, rev))
        dbconn.commit()
        return

    # organize build results by job type
    build_results = {}
    for build_id in builds:
        build_info = selfserve.build_info(auth, tree, build_id)
        buildername = build_info['buildername']
        build_results.setdefault(buildername, []).append(build_info)

    all_passed = True
    for buildername in build_results:
        passes = [x for x in build_results[buildername] if x['status'] == 0]
        fails = [x for x in build_results[buildername] if x['status'] == 1]
        #TODO: cancelled jobs imply cancel autoland

        if len(fails) == 1 and len(passes) < 2:
            logger.debug('autoland request %s %s needs to retry job for %s' % (tree, rev, buildername))
            all_passed = False
            handle_failure(logger, auth, dbconn, tree, rev, fails[0]['build_id'])
        elif len(fails) == 2:
            all_passed = False
            logger.debug('autoland request %s %s has too many failures for %s' % (tree, rev, buildername))
            query = """
                update AutolandRequest set can_be_landed=FALSE,last_updated=%s
                where tree=%s and revision=%s
            """
            cursor.execute(query, (datetime.datetime.now(), tree, rev))
            dbconn.commit()
            # TODO: post notification to bug
            #       maybe should look at all failures for better reporting
            break

    if all_passed:
        return handle_landing(logger, dbconn, tree, rev)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default='dbname=autoland user=autoland host=localhost password=autoland',
                        help="Postgresql DSN connection string")
    commandline.add_logging_group(parser)
    args = parser.parse_args()

    logging.basicConfig()
    logger = commandline.setup_logging('autoland', vars(args), {})
    logger.debug('starting autoland')

    auth = selfserve.read_credentials()
    dbconn = psycopg2.connect(args.dsn)

    # this should exceed the stable delay in buildapi
    stable_delay = datetime.timedelta(minutes=5)
    old_job = datetime.timedelta(minutes=30)

    while True:
        cursor = dbconn.cursor()
        now = datetime.datetime.now()

        # handle potentially finished autoland jobs
        query = """select tree,revision from AutolandRequest
                   where pending=0 and running=0 and last_updated<=%(time)s
                   and can_be_landed is null"""
        cursor.execute(query, ({'time': now - stable_delay}))
        for row in cursor.fetchall():
            tree, rev = row
            handle_autoland_request(logger, auth, dbconn, tree, rev)

        # we also look for any older jobs - maybe something got missed
        # in pulse
        query = """select tree,revision from AutolandRequest
                   where last_updated<=%(time)s
                   and can_be_landed is null"""
        cursor.execute(query, ({'time': now - old_job}))
        for row in cursor.fetchall():
            tree, rev = row
            handle_autoland_request(logger, auth, dbconn, tree, rev)

        time.sleep(30)
 
if __name__ == "__main__":
    main()
