import copy
import os
import sys
import unittest

HERE = os.path.split(os.path.realpath(__file__))[0]

SYS_PATH = copy.copy(sys.path)
sys.path.append(os.path.join(os.path.split(HERE)[0], 'autoland'))
import autoland
sys.path = SYS_PATH


class TestAutoland(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
