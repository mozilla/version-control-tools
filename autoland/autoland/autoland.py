#!/usr/bin/env python
import argparse
import datetime
import json
import logging
import psycopg2
import re
import requests
import sys
import time
import traceback

from mozlog.structured import (
    commandline,
    formatters,
    handlers,
    structuredlog,
)

import bugzilla
import mercurial
import mozilla_ldap
import selfserve
import transplant

BUGZILLA_COMMENT_LIMIT = 10  # max comments to post / iteration

def handle_single_failure(logger, auth, dbconn, tree, rev, buildername, build_id):
    logger.debug('autoland request %s %s needs to retry job for %s' % (tree, rev, buildername))
    job_id = selfserve.rebuild_job(auth, tree, build_id)
    if job_id:
        logger.info('submitted rebuild request %s for autoland job %s %s' % (job_id, tree, rev))
        cursor = dbconn.cursor()
        query = """
            update Autoland set last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
    else:
        logger.info('could not rebuild %s for autoland job %s %s' % (build_id, tree, rev))


def handle_insufficient_permissions(logger, dbconn, tree, rev, bugid, blame):
    cursor = dbconn.cursor()
    query = """
        update Autoland set can_be_landed=false, last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()

    comment = 'Autoland request failed. User %s has insufficient permissions to land on tree %s.' %  (blame, tree)
    add_bugzilla_comment(dbconn, bugid, comment)

def handle_failure(logger, dbconn, tree, rev, bugid, buildernames):
    logger.info('autoland request %s %s has too many failures for %s' % (tree, rev, ', '.join(buildernames)))

    cursor = dbconn.cursor()
    query = """
        update Autoland set can_be_landed=FALSE,last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()

    #TODO: add treeherder/tbpl link for job
    comment = 'Autoland request failed. Too many failures for %s.' %  (', '.join(buildernames))
    add_bugzilla_comment(dbconn, bugid, comment)

def handle_can_be_landed(logger, dbconn, tree, rev):
    logger.info('autoland request %s %s can be landed' % (tree, rev))
    cursor = dbconn.cursor()
    query = """
        update Autoland set can_be_landed=true,last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()

def handle_pending_transplants(logger, dbconn):
    cursor = dbconn.cursor()
    query = """
        select tree,revision,bugid from Autoland
        where can_be_landed is true and landed is null
    """
    cursor.execute(query)

    landed = []
    for row in cursor.fetchall():
        tree, rev, bugid = row

        pushlog = mercurial.get_pushlog(tree, rev)
        if not pushlog:
            logger.debug('could not get pushlog for tree: %s rev %s' % (tree, rev))
            return

        changesets = []
        for key in pushlog:
            for changeset in pushlog[key]['changesets']:
                # we assume by convention head revision is empty and should
                # not be landed
                if changeset != rev:
                    changesets.append(changeset)

        # TODO: allow for transplant to other trees than 'mozilla-inbound'
        result = transplant.transplant(tree, 'mozilla-inbound', changesets)

        if not result:
            logger.debug('could not connect to transplant server: tree: %s rev %s' % (tree, rev))
            continue

        if 'error' in result:
            succeeded = False
            logger.info('transplant failed: tree: %s rev: %s error: %s' % (tree, rev, json.dumps(result)))
            comment = 'Autoland request failed: could not transplant: %s' % result['error']
        else:
            succeeded = True
            comment = 'Autoland request succeeded: mozilla-inbound tip: %s' % result['tip']

        landed.append([succeeded, json.dumps(result), datetime.datetime.now(), tree, rev])
        add_bugzilla_comment(dbconn, bugid, comment)

    if landed:
        query = """
            update Autoland set landed=%s,transplant_result=%s,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.executemany(query, landed)
        dbconn.commit()

def handle_autoland_request(logger, auth, dbconn, tree, rev):

    logger.info('looking at autoland request %s %s' % (tree, rev))

    status = selfserve.job_is_done(auth, tree, rev)
    if not status:
        logger.debug('could not get job status for %s %s' % (tree, rev))
        return

    cursor = dbconn.cursor()
    if not status['job_complete']:
        logger.debug('autoland request %s %s job not complete' % (tree, rev))
        # update pending so we won't look at this job again
        # until we get another update over pulse
        query = """
            update Autoland set pending=null,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
        return

    query = """
        select bugid, blame from Autoland
        where tree=%s and revision=%s
    """
    cursor.execute(query, (tree, rev))
    bugid, blame = cursor.fetchone()

    # check ldap group
    blame = blame.strip('{}')
    result = mozilla_ldap.check_group(mozilla_ldap.read_credentials(),
                                      'scm_level_3', blame)
    if result is None:
        # can't check credentials right now, we'll try again later
        logger.info('could not check ldap group')
        return

    if not result:
        handle_insufficient_permissions(logger, dbconn, tree, rev, bugid, blame)
        return

    # everything passed, so we can land
    if status['job_passed']:
        return handle_can_be_landed(logger, dbconn, tree, rev)

    pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)

    if not builds:
        logger.debug('could not get jobs for revision')
        return

    if len(pending) > 0 or len(running) > 0:
        logger.info('autoland request %s %s still has pending or running jobs: %d %d' % (tree, rev, len(pending), len(running)))
        query = """
            update Autoland set pending=%s,running=%s,
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
        if not build_info:
            logger.debug('could not get build_info for build: %s' % build_id)
            return

        buildername = build_info['buildername']
        build_results.setdefault(buildername, []).append(build_info)

    if len(build_results) == 0:
        logger.debug('no build results')
        return

    single_failures = []
    double_failures = []
    for buildername in build_results:
        passes = [x for x in build_results[buildername] if x['status'] == 0]
        fails = [x for x in build_results[buildername] if x['status'] in [1, 2]]
        #TODO: cancelled jobs imply cancel autoland
        print(buildername, len(passes), len(fails))

        if len(fails) == 1 and not passes:
            build_id = fails[0]['build_id']
            single_failures.append((buildername, build_id))
        elif len(fails) == 2:
            build_id = fails[0]['build_id']
            double_failures.append(buildername)

    # if there are double failures, the autoland request has failed
    if double_failures:
        return handle_failure(logger, dbconn, tree, rev, bugid, double_failures)

    # single failures need to be retried
    for failure in single_failures:
        buildername, build_id = failure
        handle_single_failure(logger, auth, dbconn, tree, rev, buildername, build_id)

    # if no failures, we can land
    if not single_failures:
        return handle_can_be_landed(logger, dbconn, tree, rev)

def add_bugzilla_comment(dbconn, bugid, comment):
    cursor = dbconn.cursor()
    query = """insert into BugzillaComment(bugid, bug_comment)
               values(%s, %s)"""
    cursor.execute(query, (bugid, comment))
    dbconn.commit()

def handle_pending_bugzilla_comments(logger, dbconn):
    cursor = dbconn.cursor()
    query = """select sequence, bugid, bug_comment from BugzillaComment
               order by sequence limit %(limit)s"""
    cursor.execute(query, {'limit': BUGZILLA_COMMENT_LIMIT})

    token = bugzilla.login()
    if not token:
        logger.debug('bugzilla authentication failure')
        return

    to_delete = []
    for row in cursor.fetchall():
        sequence, bugid, comment = row
        bugid = str(bugid)
        result = bugzilla.add_comment(token, bugid, comment)
        if not result:
            logger.debug('could not post bugzilla comment to bug %s' % bugid)
        to_delete.append([sequence])

    query = """delete from BugzillaComment where sequence = %s"""
    cursor.executemany(query, to_delete)
    dbconn.commit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default='dbname=autoland user=autoland host=localhost password=autoland',
                        help="Postgresql DSN connection string")
    commandline.add_logging_group(parser)
    args = parser.parse_args()

    logging.basicConfig()
    logger = commandline.setup_logging('autoland', vars(args), {})
    logger.info('starting autoland')

    auth = selfserve.read_credentials()
    if auth is None:
        logger.critical('could not read selfserve credentials. aborting')
        return

    dbconn = psycopg2.connect(args.dsn)

    # this should exceed the stable delay in buildapi
    stable_delay = datetime.timedelta(minutes=5)
    old_job = datetime.timedelta(minutes=30)

    while True:
        try:
            cursor = dbconn.cursor()
            now = datetime.datetime.now()

            # handle potentially finished autoland jobs
            query = """select tree,revision from Autoland
                       where pending=0 and running=0 and last_updated<=%(time)s
                       and can_be_landed is null"""
            cursor.execute(query, ({'time': now - stable_delay}))
            for row in cursor.fetchall():
                tree, rev = row
                handle_autoland_request(logger, auth, dbconn, tree, rev)

            # we also look for any older jobs - maybe something got missed
            # in pulse
            query = """select tree,revision from Autoland
                       where last_updated<=%(time)s
                       and can_be_landed is null"""
            cursor.execute(query, ({'time': now - old_job}))
            for row in cursor.fetchall():
                tree, rev = row
                handle_autoland_request(logger, auth, dbconn, tree, rev)

            #
            handle_pending_bugzilla_comments(logger, dbconn)

            #
            handle_pending_transplants(logger, dbconn)

            time.sleep(30)

        except KeyboardInterrupt:
            break
        except:
            t, v, tb = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(t, v, tb)))

if __name__ == "__main__":
    main()
