import json
import logging
import os
import psycopg2
import responses
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'autoland'))
import autoland


class TestAutoland(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
