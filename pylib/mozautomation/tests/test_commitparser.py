# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# flake8: noqa

import os
import unittest
import sys

HERE = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.split(HERE)[0])


from mozautomation.commitparser import (
    parse_backouts,
    parse_bugs,
    parse_requal_reviewers,
    parse_reviewers,
    parse_rquestion_reviewers,
    replace_reviewers,
    strip_commit_metadata,
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
        self.assertEqual(list(parse_reviewers('Bug 1 - More stuff; r?romulus, ux-r=test-only')), ['romulus'])

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

        # oddball real-world examples
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

        self.assertEqual(list(parse_reviewers(
             'Bug 1181382: move declaration into namespace to resolve conflict. r=hsinyi. try: -b d -p all -u none -t none')),
             ['hsinyi'])

        self.assertEqual(list(parse_reviewers(
            'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            ['bsmedberg'])

        self.assertEqual(list(parse_reviewers(
            'Bug 1199050 - Round off the corners of browser-extension-panel\'s content. ui-r=maritz, r=gijs')),
            ['maritz', 'gijs'])

        self.assertEqual(list(parse_reviewers(
            'Bug 1197422 - Part 2: [webext] Implement the pageAction API. r=billm ui-r=bwinton')),
            ['billm', 'bwinton'])

        # 'ui-reviewer=' isn't supported (less than 4% of ui-review commits use
        # it, 'ui-r=' being the preferred syntax)
        self.assertEqual(list(parse_reviewers(
            'Bug 1217369 - "Welcome to ..." has extra padding on Loop''s standalone UI making it feel strange. r=mikedeboer,ui-review=sevaan')),
            ['mikedeboer'])

        self.assertEqual(list(parse_reviewers(
            'Bug 1182996 - Fix and add missing namespace comments. rs=ehsan\n'
            'run-clang-tidy.py \\\n'
            '-checks=\'-*,llvm-namespace-comment\' \\\n'
            '-header-filter=^/.../mozilla-central/.* \\\n'
            '-fix')),
            ['ehsan'])


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

        # oddball real-world examples
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

        self.assertEqual(list(parse_requal_reviewers(
             'Bumping gaia.json for 2 gaia revision(s) a=gaia-bump\n'
             '\n'
             'https://hg.mozilla.org/integration/gaia-central/rev/2b738dae9970\n'
             'Author: Francisco Jordano <arcturus@ardeenelinfierno.com>\n'
             'Desc: Merge pull request #30407 from arcturus/fix-contacts-test\n'
             'Fixing form test for date fields r=me\n')),
             [])

        self.assertEqual(list(parse_requal_reviewers(
            'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            ['bsmedberg'])

    def test_rquestion_reviewers(self):

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - some stuff; r?romulus')), ['romulus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r?romulus, r?remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r?romulus,r?remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r?romulus, remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r?romulus,remus')), ['romulus', 'remus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; (r?romulus)')), ['romulus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; (r?romulus,remus)')),['romulus', 'remus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; [r?romulus]')), ['romulus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; [r?remus, r?romulus]')), ['remus', 'romulus'])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r?romulus, a=test-only')), ['romulus'])

        # now with r= review granted syntax
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - some stuff; r=romulus')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r=romulus, r=remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r=romulus,r=remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r=romulus, remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r=romulus,remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; (r=romulus)')),[])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; (r=romulus,remus)')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; [r=romulus]')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; [r=remus, r=romulus]')), [])
        self.assertEqual(list(parse_rquestion_reviewers('Bug 1 - More stuff; r=romulus, a=test-only')), [])

        # oddball real-world examples
        self.assertEqual(list(parse_rquestion_reviewers(
            'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            '- Relevant spec text:\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            [])

        self.assertEqual(list(parse_rquestion_reviewers(
            'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            [])

        self.assertEqual(list(parse_rquestion_reviewers(
             'Bumping gaia.json for 2 gaia revision(s) a=gaia-bump\n'
             '\n'
             'https://hg.mozilla.org/integration/gaia-central/rev/2b738dae9970\n'
             'Author: Francisco Jordano <arcturus@ardeenelinfierno.com>\n'
             'Desc: Merge pull request #30407 from arcturus/fix-contacts-test\n'
             'Fixing form test for date fields r=me\n')),
             [])

        self.assertEqual(list(parse_rquestion_reviewers(
            'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            [])

    def test_replace_reviewers(self):
        # first with r? reviewer request syntax
        self.assertEqual(replace_reviewers('Bug 1 - some stuff; r?romulus', ['remus']), 'Bug 1 - some stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus, r?remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus,r?remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus, remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus,remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; (r?romulus)', ['remus']), 'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; (r?romulus,remus)', ['remus']), 'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; [r?romulus]', ['remus']), 'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; [r?remus, r?romulus]', ['remus']), 'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus, a=test-only', ['remus']), 'Bug 1 - More stuff; r=remus, a=test-only')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r?romulus, ux-r=test-only', ['remus', 'romulus']), 'Bug 1 - More stuff; r=remus,romulus, ux-r=test-only')

        # now with r= review granted syntax
        self.assertEqual(replace_reviewers('Bug 1 - some stuff; r=romulus', ['remus']), 'Bug 1 - some stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r=romulus, r=remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r=romulus,r=remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r=romulus, remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r=romulus,remus', ['remus']), 'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; (r=romulus)',['remus']), 'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; (r=romulus,remus)', ['remus']), 'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; [r=romulus]', ['remus']), 'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; [r=remus, r=romulus]', ['remus']), 'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff; r=romulus, a=test-only', ['remus']), 'Bug 1 - More stuff; r=remus, a=test-only')

        # try some other separators than ;
        self.assertEqual(replace_reviewers('Bug 1 - some stuff r=romulus', ['remus']), 'Bug 1 - some stuff r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff. r=romulus, r=remus', ['remus']), 'Bug 1 - More stuff. r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff - r=romulus,r=remus', ['remus']), 'Bug 1 - More stuff - r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff, r=romulus, remus', ['remus']), 'Bug 1 - More stuff, r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff.. r=romulus,remus', ['remus']), 'Bug 1 - More stuff.. r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff | (r=romulus)',['remus']), 'Bug 1 - More stuff | (r=remus)')

        # make sure things work with different spacing
        self.assertEqual(replace_reviewers('Bug 1 - some stuff;r=romulus,r=remus', ['remus']), 'Bug 1 - some stuff;r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff.r=romulus, r=remus', ['remus']), 'Bug 1 - More stuff.r=remus')
        self.assertEqual(replace_reviewers('Bug 1 - More stuff,r=romulus, remus', ['remus']), 'Bug 1 - More stuff,r=remus')

        self.assertEqual(replace_reviewers(
            'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            '- Relevant spec text:\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n',
            ['remus']),
            'Bug 1094764 - Implement AudioContext.suspend and friends.  r=remus\n'
            '- Relevant spec text:\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            '- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise')

        self.assertEqual(replace_reviewers(
            'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz',
            ['remus']),
            'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            'r=remus, sr=dbaron, a1.9=bz')

        self.assertEqual(replace_reviewers(
            'Bug 1 - blah r?dminor, r?gps, r?abc, sr=abc',
            ['dminor', 'glob', 'gps', 'abc']),
            'Bug 1 - blah r=dminor,glob,gps,abc, sr=abc')

        self.assertEqual(replace_reviewers(
            'Bug 1 - blah r?dminor r?gps r?abc sr=abc',
            ['dminor', 'glob', 'gps', 'abc']),
            'Bug 1 - blah r=dminor,glob,gps,abc sr=abc')

        self.assertEqual(replace_reviewers(
            'Bug 1 - blah r?dminor,r?gps,r?abc,sr=abc',
            ['dminor', 'glob', 'gps', 'abc']),
            'Bug 1 - blah r=dminor,glob,gps,abc,sr=abc')

        self.assertEqual(replace_reviewers('Bug 123 - Blah blah; r=gps DONTBUILD (NPOTB)', ['remus']), 'Bug 123 - Blah blah; r=remus DONTBUILD (NPOTB)')
        self.assertEqual(replace_reviewers('Bug 123 - Blah blah; r=gps DONTBUILD', ['remus']), 'Bug 123 - Blah blah; r=remus DONTBUILD')
        self.assertEqual(replace_reviewers('Bug 123 - Blah blah; r=gps (DONTBUILD)', ['remus']), 'Bug 123 - Blah blah; r=remus (DONTBUILD)')


    def test_backout_missing(self):
        self.assertIsNone(parse_backouts('Bug 1 - More stuff; r=romulus'))

    def test_backout_single(self):
        self.assertEqual(
            parse_backouts('Backed out changeset 6435d5aab611 (bug 858680)'),
            (['6435d5aab611'], [858680]))
        self.assertEqual(parse_backouts(
            'Backed out changeset 2f9d54c153ed on CLOSED TREE (bug 1067325)'),
            (['2f9d54c153ed'], [1067325]))
        self.assertEqual(
            parse_backouts('Backout b8601df335c1 (Bug 1174857) for bustage'),
            (['b8601df335c1'], [1174857]))

        self.assertEqual(
            parse_backouts('Back out b8601df335c1 (Bug 1174857) for bustage'),
            (['b8601df335c1'], [1174857]))

    def test_backout_multiple_changesets(self):
        self.assertEqual(parse_backouts(
            'Backed out changesets 4b6aa5c0a1bf and fdf38a41d92b '
            '(bug 1150549) for Mulet crashes.'),
            (['4b6aa5c0a1bf', 'fdf38a41d92b'], [1150549]))

        self.assertEqual(parse_backouts(
            'Back out changesets ed293fc9596c and f18cb4c41578 '
            '(bug 1174700) for fatal assertions in all Windows debug '
            'reftest runs.'),
            (['ed293fc9596c', 'f18cb4c41578'], [1174700]))

    def test_backout_n_changesets(self):
        self.assertEqual(parse_backouts(
            'Backed out 6 changesets (bug 1164777, bug 1163207, bug 1156914, '
            'bug 1164778) for SM(cgc) caused by something in the push.'),
            ([], [1164777, 1163207, 1156914, 1164778]))

    def test_strip_commit_metadata(self):
        self.assertEqual(strip_commit_metadata('foo'), 'foo')

        self.assertEqual(strip_commit_metadata('foo\n\nbar'), 'foo\n\nbar')

        self.assertEqual(strip_commit_metadata(
            'Bug 1 - foo\n\nMozReview-Commit-ID: abcdef'),
            'Bug 1 - foo')

        self.assertEqual(strip_commit_metadata(
            'Bug 1 - foo\n\nMore description\n\nFoo-Bar: baz\n\n'),
            'Bug 1 - foo\n\nMore description')

        self.assertEqual(strip_commit_metadata(
            'Bug 1 - foo\n\nMozReview-Commit-ID: abcdef\n\nTrailing desc'),
            'Bug 1 - foo\n\n\nTrailing desc')

        # unicode in should get unicode out
        res = strip_commit_metadata(u'foo\n\nbar')
        self.assertEqual(res, u'foo\n\nbar')
        self.assertIsInstance(res, unicode)
