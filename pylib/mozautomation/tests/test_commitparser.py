# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from mozautomation.commitparser import parse_bugs


class TestBugParsing(unittest.TestCase):
    def test_bug(self):
        self.assertEqual(parse_bugs('bug 1'), [1])
        self.assertEqual(parse_bugs('bug 123456'), [123456])
        self.assertEqual(parse_bugs('testb=1234x'), [])
        self.assertEqual(parse_bugs('ab4665521e2f'), [])
        self.assertEqual(parse_bugs('Aug 2008'), [])
        self.assertEqual(parse_bugs('b=#12345'), [12345])
        self.assertEqual(parse_bugs('GECKO_191a2_20080815_RELBRANCH'), [])
        self.assertEqual(parse_bugs('12345 is a bug'), [12345])
        self.assertEqual(parse_bugs(' 123456 whitespace!'), [123456])
