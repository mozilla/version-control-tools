import gzip
import json
import logging
import psycopg2
import unittest
import responses

import autoland_pulse

class DummyMessage(object):
    def ack(self):
        pass

class TestAutolandPulse(unittest.TestCase):

    def clear_database(self):
        cursor = self.dbconn.cursor()
        cursor.execute('delete from Autoland')
        self.dbconn.commit()

    def setUp(self):
        dsn = 'dbname=testautoland user=autoland host=localhost password=autoland'
        self.dbconn = psycopg2.connect(dsn)
        self.clear_database()

        autoland_pulse.dbconn = self.dbconn
        autoland_pulse.logger = logging.getLogger(__name__)

    def test_extract_bugid(self):
        with open('test-data/comments.json') as f:
            comments = json.load(f)
            for comment in comments:
                bugid = autoland_pulse.extract_bugid(comment['comment'])
                self.assertEqual(bugid, comment['bugid'], '%s should match %s' %
                    (bugid, comment['bugid']))

    def test_is_known_autoland_job(self):
        tree = 'try'
        rev = 'd28403874a12f2f5449190ce267a58d7abab350a'
        query = """insert into Autoland(tree, revision)
                   values(%s, %s)
        """
        cursor = self.dbconn.cursor()
        cursor.execute(query, (tree, rev))
        self.dbconn.commit()

        # we need to match "short" revisions against the full string
        for i in xrange(0, len(rev) + 1):
            short = rev[:i]
            known = autoland_pulse.is_known_autoland_job(self.dbconn, tree, short)
            self.assertTrue(known, "%s should be a known revision" % short)

        # and other revisions shouldn't match
        revs = ['923dbd546a96',
                'a540c81247c5a19486c4436228a11b030a17b1f8',
                'e42e0e8f37912d4c10f3bac1a6dac6ad630ad3cc',
                'd774d40a0521',
                'd28403874a13']
        for rev in revs:
            known = autoland_pulse.is_known_autoland_job(self.dbconn, tree, rev)
            self.assertFalse(known, '%s should not be a known revision' % rev)

    @responses.activate
    def test_autoland_messages(self):

        # set up responses for selfserve.jobs_for_revision
        with open('test-data/selfserve-jobs-for-revision.html') as f:
            jobs_for_revision = f.read()
        responses.add(responses.GET, 'https://secure.pub.build.mozilla.org/buildapi/self-serve/try/rev/7dda5def66faf5d9d0173aed32d33c964247daf3',
            body=jobs_for_revision, status=200,
            content_type='application/json', match_querystring=True)
        responses.add(responses.GET, 'https://secure.pub.build.mozilla.org/buildapi/self-serve/try/rev/7dda5def66fa',
            body=jobs_for_revision, status=200,
            content_type='application/json', match_querystring=True)

        # read and replay canned messages
        cursor = self.dbconn.cursor()
        with gzip.open('test-data/pulse-messages.json.gz') as f:
            message_data = json.load(f)
        for i, data in enumerate(message_data):
            autoland_pulse.handle_message(data, DummyMessage())

            cursor.execute('select pending,running,builds from Autoland')
            if i < 176:
                self.assertEqual(cursor.rowcount, 0, 'should be no autoland jobs')
            else:
                self.assertEqual(cursor.rowcount, 1, 'autoland job not found')
                pending, running, builds = cursor.fetchone()

                if i < 5307:
                    self.assertIsNone(pending, "pending should be none")
                    self.assertIsNone(running, "running should be none")
                    self.assertIsNone(builds, "builds should be none")
                else:
                    self.assertEqual(pending, 0, "pending should be 0")
                    self.assertEqual(running, 0, "running should be 0")
                    self.assertEqual(builds, 4, "builds should be 4")

if __name__ == '__main__':
    unittest.main()
