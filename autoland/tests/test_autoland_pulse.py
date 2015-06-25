import copy
import gzip
import json
import mock
import os
import unittest
import sys

HERE = os.path.split(os.path.realpath(__file__))[0]

SYS_PATH = copy.copy(sys.path)
sys.path.append(os.path.join(os.path.split(HERE)[0], 'autoland'))
import autoland_pulse
sys.path = SYS_PATH


class TestAutolandPulse(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
