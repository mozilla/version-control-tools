import gzip
import json
import logging
import psycopg2
import unittest
import responses

import autoland_pulse

DSN = 'dbname=testautoland user=autoland host=localhost password=autoland'


class DummyMessage(object):
    def ack(self):
        pass


class TestAutolandPulse(unittest.TestCase):

    def clear_database(self):
        cursor = self.dbconn.cursor()
        cursor.execute('delete from Testrun')
        cursor.execute('delete from Transplant')
        self.dbconn.commit()

    def setUp(self):
        self.dbconn = psycopg2.connect(DSN)
        self.clear_database()

        autoland_pulse.dbconn = self.dbconn
        autoland_pulse.logger = logging.getLogger(__name__)

    def test_is_known_testrun(self):
        tree = 'try'
        rev = 'd28403874a12f2f5449190ce267a58d7abab350a'
        query = """insert into Testrun(tree, revision)
                   values(%s, %s)
        """
        cursor = self.dbconn.cursor()
        cursor.execute(query, (tree, rev))
        self.dbconn.commit()

        # we need to match "short" revisions against the full string
        for i in xrange(autoland_pulse.REV_LENGTH, len(rev) + 1):
            short = rev[:i]
            known = autoland_pulse.is_known_testrun(self.dbconn, tree,
                                                         short)
            self.assertTrue(known, "%s should be a known revision" % short)

        # and other revisions shouldn't match
        revs = ['923dbd546a96',
                'a540c81247c5a19486c4436228a11b030a17b1f8',
                'e42e0e8f37912d4c10f3bac1a6dac6ad630ad3cc',
                'd774d40a0521',
                'd28403874a13']
        for rev in revs:
            known = autoland_pulse.is_known_testrun(self.dbconn, tree, rev)
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

        # insert a testrun which we care about
        query = 'insert into Testrun(tree,revision) values(%s,%s)'
        cursor.execute(query, ('try', '7dda5def66fa'))
        self.dbconn.commit()

        for i, data in enumerate(message_data):
            autoland_pulse.handle_message(data, DummyMessage())

            cursor.execute('select tree,revision from Testrun')
            if i >= 176:
                self.assertEqual(cursor.rowcount, 1, 'testrun not found')
                cursor.execute('select pending,running,builds from Testrun')
                pending, running, builds = cursor.fetchone()

                self.assertEqual(pending, 0, "pending should be 0")
                self.assertEqual(running, 0, "running should be 0")
                self.assertEqual(builds, 4, "builds should be 4")

if __name__ == '__main__':
    unittest.main()
