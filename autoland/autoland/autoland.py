#!/usr/bin/env python
import argparse
import bugsy
import config
import datetime
import github
import json
import logging
import mozreview
import os
import psycopg2
import sys
import time
import traceback

sys.path.insert(0, os.path.normpath(os.path.join(os.path.normpath(
                os.path.abspath(os.path.dirname(__file__))), '..', '..',
                'pylib', 'mozautomation')))
from mozautomation.commitparser import parse_bugs
from mozlog.structured import commandline

import selfserve
import transplant
import treestatus

GITHUB_COMMENT_LIMIT = 10  # max updates to post to github / iteration
MOZREVIEW_COMMENT_LIMIT = 10  # max updates to post to reviewboard / iteration

# this should exceed the stable delay in buildapi
STABLE_DELAY = datetime.timedelta(minutes=5)
OLD_JOB = datetime.timedelta(minutes=30)


def handle_pending_mozreview_pullrequests(logger, dbconn):
    gh = github.connect()
    if not gh:
        return

    bzurl = config.get('bugzilla')['url']

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

        logger.info('attempting to import pullrequest: %s' % transplant_id)

        # see if we can extract the bug from the commit message
        if bugid is None:
            title, body = github.retrieve_issue(gh, ghuser, repo, pullrequest)
            bugs = parse_bugs(title)
            if bugs:
                bugid = bugs[0]
                logger.info('using bug %s from issue title' % bugid)
                landed_revisions.append([bugid, None, None, transplant_id])

        # still no luck, attempt to autofile a bug on the user's behalf
        if bugid is None:
            logger.info('attempting to autofile bug for: %s' % transplant_id)

            b = bugsy.Bugsy(userid=bzuserid, cookie=bzcookie,
                            bugzilla_url=bzurl)
            if not b:
                logger.info('could not connect to bugzilla instance at %s for '
                            'pullrequest id %s' % (bzurl, transplant_id))
                error = 'could not connect to bugzilla. bad credentials?'
            else:
                bug = bugsy.Bug()

                # Summary is required, the rest have defaults or are optional
                bug.summary = title

                if config.testing():
                    bug.product = 'TestProduct'
                    bug.component = 'TestComponent'
                else:
                    # TODO: determine a better product & component than the
                    # defaults provided by Bugsy
                    pass

                pr_url = github.url_for_pullrequest(ghuser,repo, pullrequest)
                bug.add_comment('%s\n\nImported from: %s' % (body, pr_url))

                try:
                    b.put(bug)
                    bugid = bug.id
                    logger.info('created bug: %s ' % bugid)
                    landed_revisions.append([bugid, None, None, transplant_id])
                except bugsy.BugsyException as e:
                    logger.info('transplant failed: could not create new bug: %s '
                                % e.msg)
                    landed_revisions.append([None, False, e.msg, transplant_id])

                    # set up data to be posted back to mozreview
                    data = {
                        'request_id': transplant_id,
                        'bugid': None,
                        'landed': False,
                        'error_msg': 'could not create new bug: ' + e.msg,
                        'result': ''
                    }

                    mozreview_updates.append([transplant_id, pingback_url,
                                              json.dumps(data)])

        landed, result = transplant.transplant_to_mozreview(gh, destination,
                                                            ghuser, repo,
                                                            pullrequest,
                                                            bzuserid, bzcookie,
                                                            bugid)

        if landed:
            logger.info(('transplanted from'
                         ' https://github.com/%s/%s/pull/%s'
                         ' to destination: %s new revision: %s') %
                        (ghuser, repo, pullrequest, destination, result))
        else:
            logger.info(('transplant failed'
                         ' https://github.com/%s/%s/pull/%s'
                         ' destination: %s error: %s') %
                        (ghuser, repo, pullrequest, destination, result))

        landed_revisions.append([bugid, landed, result, transplant_id])

        # set up data to be posted back to mozreview
        data = {
            'request_id': transplant_id,
            'bugid': bugid,
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
            update MozreviewPullRequest set bugid=%s,landed=%s,result=%s
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

        if not treestatus.tree_is_open(destination):
            continue

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
                if 'is CLOSED!' in result:
                    logger.info('transplant failed: tree: %s is closed - '
                                 ' retrying later.' % tree)

                    # continuing here will skip updating the autoland request
                    # so we will attempt to land it again later.
                    continue
                else:
                    logger.info('transplant failed: tree: %s rev: %s '
                                'destination: %s error: %s' %
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

    # TODO: We should use Treeherder rather than self serve for this, but
    # Treeherder wasn't deployed when this code was originally written.
    # (See Bug 1174124.)
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

        worked = github.add_issue_comment(gh, ghuser, repo, pullrequest,
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


def get_dbconn(dsn):
    dbconn = None
    while not dbconn:
        try:
            dbconn = psycopg2.connect(dsn)
        except psycopg2.OperationalError:
            time.sleep(0.1)
    return dbconn


def main():
    parser = argparse.ArgumentParser()

    dsn = config.get('database')

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

    dbconn = get_dbconn(args.dsn)
    last_error_msg = None
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
        except psycopg2.InterfaceError:
            dbconn = get_dbconn(args.dsn)
        except:
            # If things go really badly, we might see the same exception
            # thousands of times in a row. There's not really any point in
            # logging it more than once.
            error_msg = traceback.format_exc()
            if error_msg != last_error_msg:
                logger.error(error_msg)
                last_error_msg = error_msg


if __name__ == "__main__":
    main()
