import json
import logging
import psycopg2
import responses
import unittest

import autoland

DSN = 'dbname=testautoland user=autoland host=localhost password=autoland'


class TestAutoland(unittest.TestCase):

    def clear_database(self):
        cursor = self.dbconn.cursor()
        cursor.execute('delete from Testrun')
        cursor.execute('delete from Transplant')
        self.dbconn.commit()

    def setUp(self):
        self.dbconn = psycopg2.connect(DSN)
        self.clear_database()

        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        self.dbconn.close()


if __name__ == '__main__':
    unittest.main()
