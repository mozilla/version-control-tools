#!/usr/bin/env python
import argparse
import config
import datetime
import json
import logging
import mozreview
import os
import psycopg2
import sys
import time
import traceback

sys.path.insert(0, os.path.normpath(os.path.join(os.path.normpath(
                os.path.abspath(os.path.dirname(__file__))), '..',
                                                             '..',
                                                             'pylib',
                                                             'mozautomation')))

import transplant
import treestatus


# max attempts to transplant before bailing
MAX_TRANSPLANT_ATTEMPTS = 50

# max updates to post to reviewboard / iteration
MOZREVIEW_COMMENT_LIMIT = 10

# time to wait before attempting to update MozReview after a failure to post
MOZREVIEW_RETRY_DELAY = datetime.timedelta(minutes=5)

# time to wait before retrying a transplant
TRANSPLANT_RETRY_DELAY = datetime.timedelta(minutes=5)


def handle_pending_transplants(logger, dbconn):
    cursor = dbconn.cursor()
    now = datetime.datetime.now()
    query = """
        SELECT id, destination, request
        FROM Transplant
        WHERE landed IS NULL
              AND (last_updated IS NULL OR last_updated<=%(time)s)
        ORDER BY created
    """
    transplant_retry_delay = TRANSPLANT_RETRY_DELAY
    if config.testing():
        transplant_retry_delay = datetime.timedelta(seconds=1)

    cursor.execute(query, ({'time': now - transplant_retry_delay}))

    current_treestatus = {}
    finished_revisions = []
    mozreview_updates = []
    retry_revisions = []

    def handle_treeclosed(transplant_id, tree, rev, destination, trysyntax,
                          pingback_url):
        retry_revisions.append((now, transplant_id))

        data = {
            'request_id': transplant_id,
            'tree': tree,
            'rev': rev,
            'destination': destination,
            'trysyntax': trysyntax,
            'landed': False,
            'error_msg': '',
            'result': 'Tree %s is closed - retrying later.' % tree
        }
        mozreview_updates.append([transplant_id, json.dumps(data)])

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
        transplant_id, destination, request = row

        requester = request['ldap_username']
        tree = request['tree']
        rev = request['rev']
        trysyntax = request.get('trysyntax', '')
        push_bookmark = request.get('push_bookmark', '')
        pingback_url = request.get('pingback_url', '')
        commit_descriptions = request.get('commit_descriptions')
        tree_open = current_treestatus.setdefault(
            destination, treestatus.tree_is_open(destination))

        if not tree_open:
            handle_treeclosed(transplant_id, tree, rev, destination,
                              trysyntax, pingback_url)
            continue

        attempts = 0
        started = datetime.datetime.now()
        while attempts < MAX_TRANSPLANT_ATTEMPTS:
            logger.info('initiating transplant from tree: %s rev: %s '
                        'to destination: %s, attempt %s' % (
                            tree, rev, destination, attempts + 1))

            # TODO: We should break the transplant call into two steps, one
            #       to pull down the commits to transplant, and another
            #       one to rebase it and attempt to push so we don't
            #       duplicate work unnecessarily if we have to rebase more
            #       than once.
            os.environ['AUTOLAND_REQUEST_USER'] = requester
            landed, result = transplant.transplant(logger, tree,
                                                   destination, rev,
                                                   trysyntax, push_bookmark,
                                                   commit_descriptions)
            del os.environ['AUTOLAND_REQUEST_USER']

            logging.info('transplant from tree: %s rev: %s attempt: %s: %s' % (
                tree, rev, attempts + 1, result))

            if landed or 'abort: push creates new remote head' not in result:
                break

            attempts += 1

        if landed:
            logger.info('transplant successful - new revision: %s' % result)
        else:
            if 'is CLOSED!' in result:
                logger.info('transplant failed: tree: %s is closed - '
                            ' retrying later.' % tree)
                current_treestatus[destination] = False
                handle_treeclosed(transplant_id, tree, rev, destination,
                                  trysyntax, pingback_url)
                continue
            elif 'abort: push creates new remote head' in result:
                logger.info('transplant failed: we lost a push race')
                retry_revisions.append((now, transplant_id))
                continue
            elif 'unresolved conflicts (see hg resolve' in result:
                logger.info('transplant failed - manual rebase required: '
                            'tree: %s rev: %s destination: %s error: %s' %
                            (tree, rev, destination, result))
                # This is the only autoland error for which we expect the
                # user to take action. We should make things nicer than the
                # raw mercurial error.
                # TODO: sad trombone sound
                header = ('We\'re sorry, Autoland could not rebase your '
                          'commits for you automatically. Please manually '
                          'rebase your commits and try again.\n\n')
                result = header + result
            else:
                logger.info('transplant failed: tree: %s rev: %s '
                            'destination: %s error: %s' %
                            (tree, rev, destination, result))

        completed = datetime.datetime.now()
        logger.info('elapsed transplant time: %s' % (completed - started))

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

        mozreview_updates.append([transplant_id, json.dumps(data)])

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
            insert into MozreviewUpdate(transplant_id,data)
            values(%s,%s)
        """
        cursor.executemany(query, mozreview_updates)
        dbconn.commit()


def handle_pending_mozreview_updates(logger, dbconn):
    """Attempt to post updates to mozreview"""

    cursor = dbconn.cursor()
    query = """
        select MozreviewUpdate.id,transplant_id,request,data
        from MozreviewUpdate inner join Transplant
        on (Transplant.id = MozreviewUpdate.transplant_id)
        limit %(limit)s
    """
    cursor.execute(query, {'limit': MOZREVIEW_COMMENT_LIMIT})

    mozreview_auth = mozreview.read_credentials()

    updated = []
    all_posted = True
    for row in cursor.fetchall():
        update_id, transplant_id, request, data = row
        pingback_url = request.get('pingback_url')

        logger.info('trying to post mozreview update to: %s for request: %s' %
                    (pingback_url, transplant_id))

        # We allow empty pingback_urls as they make testing easier. We can
        # always check the logs for misconfigured pingback_urls.
        if pingback_url:
            status_code, text = mozreview.update_review(mozreview_auth,
                                                        pingback_url, data)
            if status_code == 200:
                updated.append([update_id])
            else:
                logger.info('failed: %s - %s' % (status_code, text))
                all_posted = False
                break
        else:
            updated.append([update_id])

    if updated:
        query = """
            delete from MozreviewUpdate
            where id=%s
        """
        cursor.executemany(query, updated)
        dbconn.commit()

    return all_posted


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
                        help='Postgresql DSN connection string')
    parser.add_argument('--log-path', default='autoland.log',
                        help='Path to which to log')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_path,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s '
                               '%(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    logger = logging.getLogger('autoland')
    logger.info('starting autoland')

    dbconn = get_dbconn(args.dsn)
    last_error_msg = None
    next_mozreview_update = datetime.datetime.now()
    while True:
        try:
            handle_pending_transplants(logger, dbconn)

            # TODO: In normal configuration, all updates will be posted to the
            # same MozReview instance, so we don't bother tracking failure to
            # post for individual urls. In the future, we might need to
            # support this.
            if datetime.datetime.now() > next_mozreview_update:
                ok = handle_pending_mozreview_updates(logger, dbconn)
                if ok:
                    next_mozreview_update += datetime.timedelta(seconds=1)
                else:
                    next_mozreview_update += MOZREVIEW_RETRY_DELAY

            time.sleep(0.1)
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
