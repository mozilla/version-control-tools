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

import transplant
import treestatus

# max updates to post to github / iteration
GITHUB_COMMENT_LIMIT = 10

# max updates to post to reviewboard / iteration
MOZREVIEW_COMMENT_LIMIT = 10

# time to wait before retrying a transplant
TRANSPLANT_RETRY_DELAY = datetime.timedelta(minutes=5)


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

    finished_revisions = []
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
                finished_revisions.append([bugid, None, None, transplant_id])

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
                    finished_revisions.append([bugid, None, None, transplant_id])
                except bugsy.BugsyException as e:
                    logger.info('transplant failed: could not create new bug: %s '
                                % e.msg)
                    finished_revisions.append([None, False, e.msg, transplant_id])

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

        finished_revisions.append([bugid, landed, result, transplant_id])

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

    if finished_revisions:
        query = """
            update MozreviewPullRequest set bugid=%s,landed=%s,result=%s
            where id=%s
        """
        cursor.executemany(query, finished_revisions)
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
    now = datetime.datetime.now()
    query = """
        select id,tree,rev,destination,trysyntax,push_bookmark,pingback_url
        from Transplant
        where landed is null and (last_updated is null
            or last_updated<=%(time)s)
    """
    transplant_retry_delay = TRANSPLANT_RETRY_DELAY
    if config.testing():
        transplant_retry_delay = datetime.timedelta(seconds=1)

    cursor.execute(query, ({'time': now - transplant_retry_delay}))

    current_treestatus = {}
    finished_revisions = []
    mozreview_updates = []
    retry_revisions = []

    # This code is a bit messy because we have to deal with the fact that the
    # the tree could close between the call to tree_is_open and when we
    # actually attempt the revision.
    #
    # We keep a list of revisions to retry called retry_revisions which we
    # append to whenever we detect a closed tree. These revisions have their
    # last_updated field updated so we will retry them after a suitable delay.
    #
    # The other list we keep is for transplant attempts that either succeeded
    # or failed due to a reason other than a closed tree, which is called
    # finished_revisions. Successful or not, we're finished with them, they
    # will not be retried.
    for row in cursor.fetchall():
        (transplant_id, tree, rev, destination, trysyntax, push_bookmark,
            pingback_url) = row

        tree_open = current_treestatus.setdefault(destination,
                                                  treestatus.tree_is_open(destination))

        if not tree_open:
            retry_revisions.append((now, transplant_id))
            continue

        landed, result = transplant.transplant(tree, destination, rev,
                                               trysyntax, push_bookmark)
        if landed:
            logger.info(('transplanted from tree: %s rev: %s'
                         ' to destination: %s new revision: %s') %
                        (tree, rev, destination, result))
        else:
            if 'is CLOSED!' in result:
                logger.info('transplant failed: tree: %s is closed - '
                            ' retrying later.' % tree)
                current_treestatus[destination] = False
                retry_revisions.append((now, transplant_id))
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

        finished_revisions.append([landed, result, transplant_id])

    if retry_revisions:
        query = """
            update Transplant set last_updated=%s
            where id=%s
        """
        cursor.executemany(query, retry_revisions)
        dbconn.commit()

    if finished_revisions:
        query = """
            update Transplant set landed=%s,result=%s
            where id=%s
        """
        cursor.executemany(query, finished_revisions)
        dbconn.commit()

    if mozreview_updates:
        query = """
            insert into MozreviewUpdate(request_id,pingback_url,data)
            values(%s,%s,%s)
        """
        cursor.executemany(query, mozreview_updates)
        dbconn.commit()


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

    dbconn = get_dbconn(args.dsn)
    last_error_msg = None
    while True:
        try:
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
