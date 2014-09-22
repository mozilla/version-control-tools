import logging
import psycopg2
import responses
import unittest

import autoland

class TestAutoland(unittest.TestCase):

    def clear_database(self):
        cursor = self.dbconn.cursor()
        cursor.execute('delete from autolandrequest')
        cursor.execute('delete from bugzillacomment')
        self.dbconn.commit()

    def setUp(self):
        dsn = 'dbname=testautoland user=autoland host=localhost password=autoland'
        self.dbconn = psycopg2.connect(dsn)
        self.clear_database()

        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        self.dbconn.close()

    def test_handle_insufficient_permissions(self):
        tree = 'try'
        rev = 'a revision' 
        bugid = '1'
        blame = 'cthulhu@mozilla.com'

        cursor = self.dbconn.cursor()
        query = """insert into AutolandRequest(tree, revision)
                   values(%s, %s)"""
        cursor.execute(query, (tree, rev))
        self.dbconn.commit()

        autoland.handle_insufficient_permissions(self.logger, self.dbconn,
            tree, rev, bugid, blame)

        query = """select can_be_landed, last_updated from AutolandRequest
                   where tree=%s and revision=%s"""
        cursor.execute(query, (tree, rev))
        can_be_landed, last_updated = cursor.fetchone()
        self.assertEqual(can_be_landed, False)
        self.assertIsNotNone(last_updated)

    def test_add_bugzilla_comment(self):
        autoland.add_bugzilla_comment(self.dbconn, '1', 'a comment')

        cursor = self.dbconn.cursor()
        cursor.execute('select bugid, bug_comment from bugzillacomment')
        bugid, bug_comment = cursor.fetchone() 
        self.assertEqual(bugid, 1, 'bugid does not match')
        self.assertEqual(bug_comment, 'a comment', 'bug comment does not match')

        self.clear_database()
        for i in xrange(0, 10):
            autoland.add_bugzilla_comment(self.dbconn, '1', 'comment %s' % i)
        cursor.execute('select bugid, bug_comment from bugzillacomment')
        self.assertEqual(cursor.rowcount, 10,
                'could not create multiple comments for same bug')
        
if __name__ == '__main__':
    unittest.main()
