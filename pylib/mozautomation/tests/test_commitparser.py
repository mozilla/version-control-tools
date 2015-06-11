# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from mozautomation.commitparser import (
    parse_backouts,
    parse_bugs,
    parse_requal_reviewers,
    parse_reviewers,
)


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

        self.assertEqual(list(parse_reviewers(
            'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            '- Relevant spec text:\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            ['roc', 'ehsan'])

        self.assertEqual(list(parse_reviewers(
            'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            ['bsmedberg', 'dbaron', 'dbaron'])

        self.assertEqual(list(parse_reviewers(
            'Bug 123 - Blah blah; r=gps DONTBUILD (NPOTB)')),
            ['gps'])

        self.assertEqual(list(parse_reviewers(
            'Bug 123 - Blah blah; r=gps DONTBUILD')),
            ['gps'])

        self.assertEqual(list(parse_reviewers(
            'Bug 123 - Blah blah; r=gps (DONTBUILD)')),
            ['gps'])

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

        self.assertEqual(list(parse_requal_reviewers(
            'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            '- Relevant spec text:\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            ['roc', 'ehsan'])

        self.assertEqual(list(parse_requal_reviewers(
            'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            ['bsmedberg', 'dbaron'])

    def test_backout_missing(self):
        self.assertIsNone(parse_backouts('Bug 1 - More stuff; r=romulus'))

    def test_backout_single(self):
        self.assertEqual(
            parse_backouts('Backed out changeset 6435d5aab611 (bug 858680)'),
            (['6435d5aab611'], [858680]))
        self.assertEqual(parse_backouts(
            'Backed out changeset 2f9d54c153ed on CLOSED TREE (bug 1067325)'),
            (['2f9d54c153ed'], [1067325]))

    def test_backout_multiple_changesets(self):
        self.assertEqual( parse_backouts(
            'Backed out changesets 4b6aa5c0a1bf and fdf38a41d92b '
            '(bug 1150549) for Mulet crashes.'),
            (['4b6aa5c0a1bf', 'fdf38a41d92b'], [1150549]))

    def test_backout_n_changesets(self):
        self.assertEqual(parse_backouts(
            'Backed out 6 changesets (bug 1164777, bug 1163207, bug 1156914, '
            'bug 1164778) for SM(cgc) caused by something in the push.'),
            ([], [1164777, 1163207, 1156914, 1164778]))

