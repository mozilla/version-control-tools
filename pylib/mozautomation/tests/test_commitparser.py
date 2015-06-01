# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from mozautomation.commitparser import (parse_bugs,
                                        parse_requal_reviewers,
                                        parse_reviewers)


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

    def test_reviewers(self):

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_reviewers('Bug 1 - some stuff; r?romulus')), ['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus, r?remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus,r?remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus, remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus,remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; (r?romulus)')),['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; (r?romulus,remus)')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; [r?romulus]')), ['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; [r?remus, r?romulus]')), ['remus', 'romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus, a=test-only')), ['romulus', 'test-only'])

        # now with r= review granted syntax
        self.assertEqual(list(parse_reviewers('Bug 1 - some stuff; r=romulus')), ['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r=romulus, r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r=romulus,r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r=romulus, remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r=romulus,remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; (r=romulus)')),['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; (r=romulus,remus)')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; [r=romulus]')), ['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; [r=remus, r=romulus]')), ['remus', 'romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r=romulus, a=test-only')), ['romulus', 'test-only'])

        # try some other separators than ;
        self.assertEqual(list(parse_reviewers('Bug 1 - some stuff r=romulus')), ['romulus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff. r=romulus, r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff - r=romulus,r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff, r=romulus, remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff.. r=romulus,remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff | (r=romulus)')),['romulus'])

        # make sure things work with different spacing
        self.assertEqual(list(parse_reviewers('Bug 1 - some stuff;r=romulus,r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff.r=romulus, r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff,r=romulus, remus')), ['romulus', 'remus'])

    def test_requal_reviewers(self):

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - some stuff; r?romulus')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r?romulus, r?remus')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r?romulus,r?remus')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r?romulus, remus')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r?romulus,remus')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; (r?romulus)')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; (r?romulus,remus)')),[])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; [r?romulus]')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; [r?remus, r?romulus]')), [])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r?romulus, a=test-only')), [])

        # now with r= review granted syntax
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - some stuff; r=romulus')), ['romulus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r=romulus, r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r=romulus,r=remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r=romulus, remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r=romulus,remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; (r=romulus)')),['romulus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; (r=romulus,remus)')), ['romulus', 'remus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; [r=romulus]')), ['romulus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; [r=remus, r=romulus]')), ['remus', 'romulus'])
        self.assertEqual(list(parse_requal_reviewers('Bug 1 - More stuff; r=romulus, a=test-only')), ['romulus'])
