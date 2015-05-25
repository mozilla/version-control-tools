#!/usr/bin/env python
import argparse
import datetime
import github
import json
import logging
import mozreview
import psycopg2
import sys
import time
import traceback

from mozlog.structured import commandline

import selfserve
import transplant

GITHUB_COMMENT_LIMIT = 10  # max updates to post to github / iteration
MOZREVIEW_COMMENT_LIMIT = 10  # max updates to post to reviewboard / iteration

# this should exceed the stable delay in buildapi
STABLE_DELAY = datetime.timedelta(minutes=5)
OLD_JOB = datetime.timedelta(minutes=30)


def handle_pending_mozreview_pullrequests(logger, dbconn):
    cursor = dbconn.cursor()

    query = """
        select id,ghuser,repo,pullrequest,destination,bzuserid,bzcookie,bugid,
               pingback_url
        from MozreviewPullRequest
        where landed is null
    """
    cursor.execute(query)

    landed_revisions = []
    mozreview_updates = []
    for row in cursor.fetchall():
        (transplant_id, ghuser, repo, pullrequest, destination, bzuserid,
         bzcookie, bugid, pingback_url) = row

        landed, result = transplant.transplant_to_mozreview(destination,
                                                            ghuser, repo,
                                                            pullrequest,
                                                            bzuserid, bzcookie,
                                                            bugid)

        if landed is None:
            logger.info(('transplant failed - could not connect to github'
                         ' for https://github.com/%s/%s/pull/%s'
                         ' to destination: %s') %
                        (ghuser, repo, pullrequest, destination))
            # we'll try again later
            break
        elif landed:
            logger.info(('transplanted from'
                         ' https://github.com/%s/%s/pull/%s'
                         ' to destination: %s new revision: %s') %
                        (ghuser, repo, pullrequest, destination, result))
        else:
            logger.info(('transplant failed'
                         ' https://github.com/%s/%s/pull/%s'
                         ' destination: %s error: %s') %
                        (ghuser, repo, pullrequest, destination, result))

        landed_revisions.append([landed, result, transplant_id])

        # set up data to be posted back to mozreview
        data = {
            'request_id': transplant_id,
            'landed': landed,
            'error_msg': '',
            'result': ''
        }

        if landed:
            data['result'] = result
        else:
            data['error_msg'] = result

        mozreview_updates.append([transplant_id, pingback_url, json.dumps(data)])

    if landed_revisions:
        query = """
            update MozreviewPullRequest set landed=%s,result=%s
            where id=%s
        """
        cursor.executemany(query, landed_revisions)
        dbconn.commit()

    if mozreview_updates:
        query = """
            insert into MozreviewUpdate(request_id,pingback_url,data)
            values(%s,%s,%s)
        """
        cursor.executemany(query, mozreview_updates)
        dbconn.commit()


def handle_pending_transplants(logger, dbconn):
    cursor = dbconn.cursor()

    query = """
        select id,tree,rev,destination,trysyntax,pingback_url
        from Transplant
        where landed is null
    """
    cursor.execute(query)

    landed_revisions = []
    mozreview_updates = []
    for row in cursor.fetchall():
        transplant_id, tree, rev, destination, trysyntax, pingback_url = row

        if destination == 'try':
            if not trysyntax.startswith("try: "):
                trysyntax =  "try: %s" % trysyntax
            landed, result = transplant.transplant_to_try(tree, rev, trysyntax)
            if landed:
                logger.info(('transplanted from tree: %s rev: %s'
                             ' to destination: %s new revision: %s') %
                            (tree, rev, destination, result))

                query = """
                    insert into Testrun(tree,revision,last_updated)
                    values(%s,%s,%s)
                """
                cursor.execute(query, ('try', result, datetime.datetime.now()))

            else:
                logger.info(('transplant failed: tree: %s rev: %s'
                             'destination: %s error: %s') %
                            (tree, rev, destination, result))

            # set up data to be posted back to mozreview
            data = {
                'request_id': transplant_id,
                'tree': tree,
                'rev': rev,
                'destination': destination,
                'trysyntax': trysyntax,
                'landed': landed,
                'error_msg': '',
                'result': ''
            }

            if landed:
                data['result'] = result
            else:
                data['error_msg'] = result

            mozreview_updates.append([transplant_id, pingback_url, json.dumps(data)])

        else:
            landed = False
            result = 'unknown destination: %s' % destination

        landed_revisions.append([landed, result, transplant_id])

    if landed_revisions:
        query = """
            update Transplant set landed=%s,result=%s
            where id=%s
        """
        cursor.executemany(query, landed_revisions)
        dbconn.commit()

    if mozreview_updates:
        query = """
            insert into MozreviewUpdate(request_id,pingback_url,data)
            values(%s,%s,%s)
        """
        cursor.executemany(query, mozreview_updates)
        dbconn.commit()


def handle_single_failure(logger, auth, dbconn, tree, rev, buildername,
                          build_id):
    """Retrigger a job for a testrun."""

    logger.debug('testrun request %s %s needs to retry job for %s' %
                 (tree, rev, buildername))
    job_id = selfserve.rebuild_job(auth, tree, build_id)
    if job_id:
        logger.info('submitted rebuild request %s for testrun job %s %s' %
                    (job_id, tree, rev))
        cursor = dbconn.cursor()
        query = """
            update Testrun set last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
    else:
        logger.info('could not rebuild %s for testrun job %s %s' %
                    (build_id, tree, rev))


def handle_failure(logger, dbconn, tree, rev, buildernames):
    """Mark testrun as not landable"""

    logger.info('testrun %s %s has too many failures for %s' %
                (tree, rev, ', '.join(buildernames)))

    cursor = dbconn.cursor()
    query = """
        update Testrun set can_be_landed=FALSE,last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()


def handle_can_be_landed(logger, dbconn, tree, rev):
    """Mark testrun as landable."""

    logger.info('testrun %s %s can be landed' % (tree, rev))
    cursor = dbconn.cursor()
    query = """
        update Testrun set can_be_landed=true,last_updated=%s
        where tree=%s and revision=%s
    """
    cursor.execute(query, (datetime.datetime.now(), tree, rev))
    dbconn.commit()


def check_testrun(logger, auth, dbconn, tree, rev):
    """Check an individual testrun and see if jobs need to be retriggered
       or we can mark it as complete """

    logger.info('looking at testrun %s %s' % (tree, rev))

    status = selfserve.job_is_done(auth, tree, rev)
    if not status:
        logger.debug('could not get job status for %s %s' % (tree, rev))
        return

    cursor = dbconn.cursor()
    if 'status' in status and status['status'] == 'FAILED':
        logger.debug('testrun %s %s is unknown' % (tree, rev))
        query = """
            update Testrun set can_be_landed=FALSE,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
        return

    if not status['job_complete']:
        logger.debug('testrun %s %s job not complete' % (tree, rev))
        # update pending so we won't look at this job again
        # until we get another update over pulse
        query = """
            update Testrun set pending=null,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (datetime.datetime.now(), tree, rev))
        dbconn.commit()
        return

    # everything passed, so we can land
    if status['job_passed']:
        return handle_can_be_landed(logger, dbconn, tree, rev)

    pending, running, builds = selfserve.jobs_for_revision(auth, tree, rev)

    if not builds:
        logger.debug('could not get jobs for revision')
        return

    if len(pending) > 0 or len(running) > 0:
        query = """
            update Testrun set pending=%s,running=%s,builds=%s,last_updated=%s
            where tree=%s and revision=%s
        """
        cursor.execute(query, (len(pending), len(running), len(builds),
                       datetime.datetime.now(), tree, rev))
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
    for builder in build_results:
        passes = [x for x in build_results[builder] if x['status'] == 0]
        fails = [x for x in build_results[builder] if x['status'] in [1, 2]]
        #TODO: cancelled jobs imply cancel autoland

        if len(fails) == 1 and not passes:
            build_id = fails[0]['build_id']
            single_failures.append((builder, build_id))
        elif len(fails) >= 2:
            build_id = fails[0]['build_id']
            double_failures.append(builder)

    # if there are double failures, the autoland request has failed
    if double_failures:
        return handle_failure(logger, dbconn, tree, rev, double_failures)

    # single failures need to be retried
    for failure in single_failures:
        buildername, build_id = failure
        handle_single_failure(logger, auth, dbconn, tree, rev, buildername,
                              build_id)

    # if no failures, we can land
    if not single_failures:
        return handle_can_be_landed(logger, dbconn, tree, rev)


def monitor_testruns(logger, auth, dbconn):
    """ Find testruns to examine for completion """

    cursor = dbconn.cursor()

    # handle potentially finished test runs
    now = datetime.datetime.now()
    query = """select tree,revision from Testrun
               where ((pending=0 and running=0 and last_updated<=%(time)s)
               or last_updated<=%(old)s)
               and can_be_landed is null"""
    cursor.execute(query, ({'time': now - STABLE_DELAY, 'old': now - OLD_JOB}))
    for row in cursor.fetchall():
        tree, rev = row
        check_testrun(logger, auth, dbconn, tree, rev)


def handle_pending_github_updates(logger, dbconn):
    """Attempt to post updates to github"""

    gh = github.connect()
    if not gh:
        return

    cursor = dbconn.cursor()
    query = """
        select id,ghuser,repo,pullrequest,destination,landed,result,pingback_url
        from MozreviewPullRequest
        where landed is not NULL and pullrequest_updated is NULL
        limit %(limit)s
    """
    cursor.execute(query, {'limit': GITHUB_COMMENT_LIMIT})

    updated = []
    for row in cursor.fetchall():
        ghuser = row[1]
        repo = row[2]
        pullrequest = row[3]
        landed = row[5]
        result = row[6]
        pingback_url = row[7]

        if landed:
            message = 'Your new review request is available at: %s' % result
        else:
            message = 'Something went wrong importing to mozreview: %s' % result

        logger.info('attempting to add comment to pullrequest for request: %s' % row[0])

        worked = github.add_pullrequest_comment(gh, ghuser, repo,
                                                pullrequest,
                                                message)
        if worked:
            updated.append([row[0]])
        else:
            logger.info('commenting on pull request failed')

    if updated:
        query = """
            update MozreviewPullRequest set pullrequest_updated=TRUE
            where id=%s
        """
        cursor.executemany(query, updated)
        dbconn.commit()


def handle_pending_mozreview_updates(logger, dbconn):
    """Attempt to post updates to mozreview"""

    cursor = dbconn.cursor()
    query = """
        select request_id,pingback_url,data
        from MozreviewUpdate
        limit %(limit)s
    """
    cursor.execute(query, {'limit': MOZREVIEW_COMMENT_LIMIT})

    mozreview_auth = mozreview.read_credentials()

    updated = []
    for row in cursor.fetchall():
        request_id, pingback_url, data = row
        logger.info('trying to post mozreview update to: %s for request: %s' %
                    (pingback_url, request_id))

        status_code, text = mozreview.update_review(mozreview_auth,
                                                    pingback_url, data)
        if status_code == 200:
            updated.append([request_id])
        else:
            logger.info('failed: %s - %s' % (status_code, text))

    if updated:
        query = """
            delete from MozreviewUpdate
            where request_id=%s
        """
        cursor.executemany(query, updated)
        dbconn.commit()


def main():
    parser = argparse.ArgumentParser()
    dsn = 'dbname=autoland user=autoland host=localhost password=autoland'
    parser.add_argument('--dsn', default=dsn,
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

    dbconn = None
    while not dbconn:
        try:
            dbconn = psycopg2.connect(args.dsn)
        except psycopg2.OperationalError:
            time.sleep(0.1)

    while True:
        try:
            monitor_testruns(logger, auth, dbconn)
            handle_pending_mozreview_pullrequests(logger, dbconn)
            handle_pending_transplants(logger, dbconn)
            handle_pending_github_updates(logger, dbconn)
            handle_pending_mozreview_updates(logger, dbconn)
            time.sleep(0.25)
        except KeyboardInterrupt:
            break
        except:
            t, v, tb = sys.exc_info()
            logger.error('\n'.join(traceback.format_exception(t, v, tb)))


if __name__ == "__main__":
    main()
