# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# flake8: noqa

import os
import unittest
import sys

HERE = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.split(HERE)[0])


from cgi import escape


from mozautomation.commitparser import (
    add_hyperlinks,
    htmlescape,
    parse_backouts,
    parse_bugs,
    parse_commit_id,
    parse_requal_reviewers,
    parse_reviewers,
    parse_rquestion_reviewers,
    replace_reviewers,
    strip_commit_metadata,
)


class TestBugParsing(unittest.TestCase):
    def test_bug(self):
        self.assertEqual(parse_bugs(b'bug 1'), [1])
        self.assertEqual(parse_bugs(b'bug 123456'), [123456])
        self.assertEqual(parse_bugs(b'testb=1234x'), [])
        self.assertEqual(parse_bugs(b'ab4665521e2f'), [])
        self.assertEqual(parse_bugs(b'Aug 2008'), [])
        self.assertEqual(parse_bugs(b'b=#12345'), [12345])
        self.assertEqual(parse_bugs(b'GECKO_191a2_20080815_RELBRANCH'), [])
        self.assertEqual(parse_bugs(b'12345 is a bug'), [12345])
        self.assertEqual(parse_bugs(b' 123456 whitespace!'), [123456])

        # Duplicate bug numbers should be stripped.
        msg = b'''Bug 1235097 - Add support for overriding the site root

On brasstacks, `web.ctx.home` is incorrect (see bug 1235097 comment 23), which
means that the URL used by mohawk to verify the authenticated request hashes
differs from that used to generate the hash.'''
        self.assertEqual(parse_bugs(msg), [1235097])

        # Merge numbers should not be considered bug numbers.
        msg = b'''servo: Merge #19754 - Implement element.innerText getter (from ferjm:innertext); r=mbrubeck

Source-Repo: https://github.com/servo/servo
Source-Revision: 9e64008e759a678a3971d04977c2b20b66fa8229'''
        self.assertEqual(parse_bugs(msg), [])

        msg = b'''Bug 123456 - Fix all of the things

Source-Repo: https://github.com/mozilla/foo'''
        self.assertEqual(parse_bugs(msg), [123456])

        msg = b'''Merge #4256

This fixes #9000 and bug 324521

Source-Repo: https://github.com/mozilla/foo'''
        self.assertEqual(parse_bugs(msg), [324521])

    def test_bug_conservatively(self):
        self.assertEqual(parse_bugs(b'bug 1', conservative=True), [1])
        self.assertEqual(parse_bugs(b'bug 123456', conservative=True), [123456])
        self.assertEqual(parse_bugs(b'Bug 123456', conservative=True), [123456])
        self.assertEqual(parse_bugs(b'debug 123456', conservative=True), [])
        self.assertEqual(parse_bugs(b'testb=1234x', conservative=True), [])
        self.assertEqual(parse_bugs(b'ab4665521e2f', conservative=True), [])
        self.assertEqual(parse_bugs(b'Aug 2008', conservative=True), [])
        self.assertEqual(parse_bugs(b'b=#12345', conservative=True), [])
        self.assertEqual(parse_bugs(b'b=12345', conservative=True), [12345])
        self.assertEqual(parse_bugs(b'GECKO_191a2_20080815_RELBRANCH', conservative=True), [])
        self.assertEqual(parse_bugs(b'12345 is a bug', conservative=True), [])
        self.assertEqual(parse_bugs(b' 123456 whitespace!', conservative=True), [])

    def test_reviewers(self):

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_reviewers(b'Bug 1 - some stuff; r?romulus')), [b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus, r?remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus,r?remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus, remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus,remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; (r?romulus)')),[b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; (r?romulus,remus)')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; [r?romulus]')), [b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; [r?remus, r?romulus]')), [b'remus', b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus, a=test-only')), [b'romulus', b'test-only'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r?romulus, ux-r=test-only')), [b'romulus'])

        # now with r= review granted syntax
        self.assertEqual(list(parse_reviewers(b'Bug 1 - some stuff; r=romulus')), [b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r=romulus, r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r=romulus,r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r=romulus, remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r=romulus,remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; (r=romulus)')),[b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; (r=romulus,remus)')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; [r=romulus]')), [b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; [r=remus, r=romulus]')), [b'remus', b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff; r=romulus, a=test-only')), [b'romulus', b'test-only'])

        # try some other separators than ;
        self.assertEqual(list(parse_reviewers(b'Bug 1 - some stuff r=romulus')), [b'romulus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff. r=romulus, r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff - r=romulus,r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff, r=romulus, remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff.. r=romulus,remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff | (r=romulus)')),[b'romulus'])

        # make sure things work with different spacing
        self.assertEqual(list(parse_reviewers(b'Bug 1 - some stuff;r=romulus,r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff.r=romulus, r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff,r=romulus, remus')), [b'romulus', b'remus'])

        # test that periods in names are OK
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff.r=jimmy.jones, r=bill.mcneal')), [b'jimmy.jones', b'bill.mcneal'])
        self.assertEqual(list(parse_reviewers(b'Bug 1 - More stuff,r=jimmy.')), [b'jimmy'])


        # check some funky names too
        self.assertEqual(list(parse_reviewers(b"stuff;r=a")), [b"a"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=aa")), [b"aa"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=.a")), [b".a"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=..a")), [b"..a"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=...a")), [b"...a"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=a...a")), [b"a...a"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=a.b")), [b"a.b"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=a.b.c")), [b"a.b.c"])
        self.assertEqual(list(parse_reviewers(b"stuff;r=-.-.-")), [b"-.-.-"])

        # NOTE: a string such as "stuff;r=a.,b" will not be parsed as expected
        # and will yield ["a"]. TODO: fix this in the future in the regex, or
        # do some post processing in `parse_reviewers` if this is needed. The
        # following test is testing the current behaviour only.

        self.assertEqual(list(parse_reviewers(b"stuff;r=a.,b")), [b"a"])

        # altogether now with some spaces sprinkled here and there
        self.assertEqual(
            list(parse_reviewers(b"hi;r=a,aa,.a,..a,...a, a...a,a.b, a.b.c, -.-.-")),
            [ b"a", b"aa", b".a", b"..a", b"...a", b"a...a", b"a.b", b"a.b.c", b"-.-.-"]
        )

        # bare r?
        self.assertEqual(list(parse_reviewers(b'Bug 123 - Blah blah; r?')), [])
        self.assertEqual(list(parse_reviewers(
            b'Bug 1313324 - Cover the screensharing UI with browser chrome test, r=')),
            [])

        # oddball real-world examples
        self.assertEqual(list(parse_reviewers(
            b'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            b'- Relevant spec text:\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            [b'roc', b'ehsan'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            b'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            b'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            [b'bsmedberg', b'dbaron', b'dbaron'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 123 - Blah blah; r=gps DONTBUILD (NPOTB)')),
            [b'gps'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 123 - Blah blah; r=gps DONTBUILD')),
            [b'gps'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 123 - Blah blah; r=gps (DONTBUILD)')),
            [b'gps'])

        self.assertEqual(list(parse_reviewers(
             b'Bug 1181382: move declaration into namespace to resolve conflict. r=hsinyi. try: -b d -p all -u none -t none')),
             [b'hsinyi'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            [b'bsmedberg'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 1199050 - Round off the corners of browser-extension-panel\'s content. ui-r=maritz, r=gijs')),
            [b'maritz', b'gijs'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 1197422 - Part 2: [webext] Implement the pageAction API. r=billm ui-r=bwinton')),
            [b'billm', b'bwinton'])

        # 'ui-reviewer=' isn't supported (less than 4% of ui-review commits use
        # it, 'ui-r=' being the preferred syntax)
        self.assertEqual(list(parse_reviewers(
            b'Bug 1217369 - "Welcome to ..." has extra padding on Loop\'s standalone UI making it feel strange. r=mikedeboer,ui-review=sevaan')),
            [b'mikedeboer'])

        self.assertEqual(list(parse_reviewers(
            b'Bug 1182996 - Fix and add missing namespace comments. rs=ehsan\n'
            b'run-clang-tidy.py \\\n'
            b'-checks=\'-*,llvm-namespace-comment\' \\\n'
            b'-header-filter=^/.../mozilla-central/.* \\\n'
            b'-fix')),
            [b'ehsan'])

    @unittest.skip
    def test_first_reviewer_with_period_at_end_of_name():
        # TODO: this is not the current behaviour, but implementing this would
        # yield more expected results. We should probably also account for the
        # case of users having a period at the end of their username.
        self.assertEqual(list(parse_reviewers(b"stuff;r=a.,b")), [b"a", b"b"])

    def test_requal_reviewers(self):
        # empty
        self.assertEqual(list(parse_requal_reviewers(b'')), [])

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - some stuff; r?romulus')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r?romulus, r?remus')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r?romulus,r?remus')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r?romulus, remus')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r?romulus,remus')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; (r?romulus)')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; (r?romulus,remus)')),[])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; [r?romulus]')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; [r?remus, r?romulus]')), [])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r?romulus, a=test-only')), [])

        # now with r= review granted syntax
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - some stuff; r=romulus')), [b'romulus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r=romulus, r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r=romulus,r=remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r=romulus, remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r=romulus,remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; (r=romulus)')),[b'romulus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; (r=romulus,remus)')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; [r=romulus]')), [b'romulus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; [r=remus, r=romulus]')), [b'remus', b'romulus'])
        self.assertEqual(list(parse_requal_reviewers(b'Bug 1 - More stuff; r=romulus, a=test-only')), [b'romulus'])

        # bare r?
        self.assertEqual(list(parse_requal_reviewers(
            b'Bug 123 - Blah blah; r?')), [])
        self.assertEqual(list(parse_requal_reviewers(
            b'Bug 1313324 - Cover the screensharing UI with browser chrome test, r=')),
            [])

        # oddball real-world examples
        self.assertEqual(list(parse_requal_reviewers(
            b'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            b'- Relevant spec text:\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            [b'roc', b'ehsan'])

        self.assertEqual(list(parse_requal_reviewers(
            b'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            b'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            b'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            [b'bsmedberg', b'dbaron'])

        self.assertEqual(list(parse_requal_reviewers(
             b'Bumping gaia.json for 2 gaia revision(s) a=gaia-bump\n'
             b'\n'
             b'https://hg.mozilla.org/integration/gaia-central/rev/2b738dae9970\n'
             b'Author: Francisco Jordano <arcturus@ardeenelinfierno.com>\n'
             b'Desc: Merge pull request #30407 from arcturus/fix-contacts-test\n'
             b'Fixing form test for date fields r=me\n')),
             [])

        self.assertEqual(list(parse_requal_reviewers(
            b'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            [b'bsmedberg'])

    def test_rquestion_reviewers(self):
        # empty
        self.assertEqual(list(parse_rquestion_reviewers(b'')), [])

        # first with r? reviewer request syntax
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - some stuff; r?romulus')), [b'romulus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r?romulus, r?remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r?romulus,r?remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r?romulus, remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r?romulus,remus')), [b'romulus', b'remus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; (r?romulus)')), [b'romulus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; (r?romulus,remus)')),[b'romulus', b'remus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; [r?romulus]')), [b'romulus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; [r?remus, r?romulus]')), [b'remus', b'romulus'])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r?romulus, a=test-only')), [b'romulus'])

        # now with r= review granted syntax
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - some stuff; r=romulus')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r=romulus, r=remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r=romulus,r=remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r=romulus, remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r=romulus,remus')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; (r=romulus)')),[])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; (r=romulus,remus)')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; [r=romulus]')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; [r=remus, r=romulus]')), [])
        self.assertEqual(list(parse_rquestion_reviewers(b'Bug 1 - More stuff; r=romulus, a=test-only')), [])

        # oddball real-world examples
        self.assertEqual(list(parse_rquestion_reviewers(
            b'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            b'- Relevant spec text:\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n')),
            [])

        self.assertEqual(list(parse_rquestion_reviewers(
            b'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            b'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            b'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz')),
            [])

        self.assertEqual(list(parse_rquestion_reviewers(
            b'Bumping gaia.json for 2 gaia revision(s) a=gaia-bump\n'
            b'\n'
            b'https://hg.mozilla.org/integration/gaia-central/rev/2b738dae9970\n'
            b'Author: Francisco Jordano <arcturus@ardeenelinfierno.com>\n'
            b'Desc: Merge pull request #30407 from arcturus/fix-contacts-test\n'
            b'Fixing form test for date fields r=me\n')),
            [])

        self.assertEqual(list(parse_rquestion_reviewers(
            b'Bug 1024110 - Change Aurora\'s default profile behavior to use channel-specific profiles. r=bsmedberg f=gavin,markh')),
            [])

    def test_replace_reviewers(self):
        # empty
        self.assertEqual(replace_reviewers(b'', [b'remus']), b'r=remus')

        # first with r? reviewer request syntax
        self.assertEqual(replace_reviewers(b'Bug 1 - some stuff; r?romulus', [b'remus']), b'Bug 1 - some stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus, r?remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus,r?remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus, remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus,remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; (r?romulus)', [b'remus']), b'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; (r?romulus,remus)', [b'remus']), b'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; [r?romulus]', [b'remus']), b'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; [r?remus, r?romulus]', [b'remus']), b'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus, a=test-only', [b'remus']), b'Bug 1 - More stuff; r=remus, a=test-only')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r?romulus, ux-r=test-only', [b'remus', b'romulus']), b'Bug 1 - More stuff; r=remus,romulus, ux-r=test-only')

        # now with r= review granted syntax
        self.assertEqual(replace_reviewers(b'Bug 1 - some stuff; r=romulus', [b'remus']), b'Bug 1 - some stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r=romulus, r=remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r=romulus,r=remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r=romulus, remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r=romulus,remus', [b'remus']), b'Bug 1 - More stuff; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; (r=romulus)',[b'remus']), b'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; (r=romulus,remus)', [b'remus']), b'Bug 1 - More stuff; (r=remus)')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; [r=romulus]', [b'remus']), b'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; [r=remus, r=romulus]', [b'remus']), b'Bug 1 - More stuff; [r=remus]')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff; r=romulus, a=test-only', [b'remus']), b'Bug 1 - More stuff; r=remus, a=test-only')

        # try some other separators than ;
        self.assertEqual(replace_reviewers(b'Bug 1 - some stuff r=romulus', [b'remus']), b'Bug 1 - some stuff r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff. r=romulus, r=remus', [b'remus']), b'Bug 1 - More stuff. r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff - r=romulus,r=remus', [b'remus']), b'Bug 1 - More stuff - r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff, r=romulus, remus', [b'remus']), b'Bug 1 - More stuff, r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff.. r=romulus,remus', [b'remus']), b'Bug 1 - More stuff.. r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff | (r=romulus)',[b'remus']), b'Bug 1 - More stuff | (r=remus)')

        # make sure things work with different spacing
        self.assertEqual(replace_reviewers(b'Bug 1 - some stuff;r=romulus,r=remus', [b'remus']), b'Bug 1 - some stuff;r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff.r=romulus, r=remus', [b'remus']), b'Bug 1 - More stuff.r=remus')
        self.assertEqual(replace_reviewers(b'Bug 1 - More stuff,r=romulus, remus', [b'remus']), b'Bug 1 - More stuff,r=remus')

        self.assertEqual(replace_reviewers(
            b'Bug 1094764 - Implement AudioContext.suspend and friends.  r=roc,ehsan\n'
            b'- Relevant spec text:\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise\n',
            [b'remus']),
            b'Bug 1094764 - Implement AudioContext.suspend and friends.  r=remus\n'
            b'- Relevant spec text:\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-suspend-Promise\n'
            b'- http://webaudio.github.io/web-audio-api/#widl-AudioContext-resume-Promise')

        self.assertEqual(replace_reviewers(
            b'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            b'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            b'r=bsmedberg/dbaron, sr=dbaron, a1.9=bz',
            [b'remus']),
            b'Bug 380783 - nsStringAPI.h: no equivalent of IsVoid (tell if '
            b'string is null), patch by Mook <mook.moz+mozbz@gmail.com>, '
            b'r=remus, sr=dbaron, a1.9=bz')

        self.assertEqual(replace_reviewers(
            b'Bug 1 - blah r?dminor, r?gps, r?abc, sr=abc',
            [b'dminor', b'glob', b'gps', b'abc']),
            b'Bug 1 - blah r=dminor,glob,gps,abc, sr=abc')

        self.assertEqual(replace_reviewers(
            b'Bug 1 - blah r?dminor r?gps r?abc sr=abc',
            [b'dminor', b'glob', b'gps', b'abc']),
            b'Bug 1 - blah r=dminor,glob,gps,abc sr=abc')

        self.assertEqual(replace_reviewers(
            b'Bug 1 - blah r?dminor,r?gps,r?abc,sr=abc',
            [b'dminor', b'glob', b'gps', b'abc']),
            b'Bug 1 - blah r=dminor,glob,gps,abc,sr=abc')

        self.assertEqual(replace_reviewers(b'Bug 123 - Blah blah; r=gps DONTBUILD (NPOTB)', [b'remus']), b'Bug 123 - Blah blah; r=remus DONTBUILD (NPOTB)')
        self.assertEqual(replace_reviewers(b'Bug 123 - Blah blah; r=gps DONTBUILD', [b'remus']), b'Bug 123 - Blah blah; r=remus DONTBUILD')
        self.assertEqual(replace_reviewers(b'Bug 123 - Blah blah; r=gps (DONTBUILD)', [b'remus']), b'Bug 123 - Blah blah; r=remus (DONTBUILD)')

        self.assertEqual(replace_reviewers(b'Bug 123 - Blah blah; r?', [b'remus']), b'Bug 123 - Blah blah; r=remus')
        self.assertEqual(replace_reviewers(b'Bug 123 - Blah blah; r? DONTBUILD', [b'remus']), b'Bug 123 - Blah blah; r=remus DONTBUILD')

    def test_backout_partial(self):
        # bug without node
        self.assertIsNone(parse_backouts(
            b'Bug 1 - More stuff; r=romulus'))

        # node without bug
        self.assertEqual(parse_backouts(
            b'Backout f484160e0a08 for causing slow heat death of the universe'),
            ([b'f484160e0a08'], []))

        # backout not on first line
        self.assertIsNone(parse_backouts(
            b'Bug 123 - Blah blah; r=gps\n'
            b'Backout ffffffffffff'))

    def test_backout_single(self):
        # b'backed out'
        self.assertEqual(parse_backouts(
            b'Backed out changeset 6435d5aab611 (bug 858680)'),
            ([b'6435d5aab611'], [858680]))

        # b'backout of'
        self.assertEqual(parse_backouts(
            b'backout of f9abb9c83452 (bug 1319111) for crashes, r=bz'),
            ([b'f9abb9c83452'], [1319111]))

        # b'backout revision'
        self.assertEqual(parse_backouts(
            b'Backout revision 20a9d741cdf4 (bug 1354641) a=me'),
            ([b'20a9d741cdf4'], [1354641]))

        # b'backout'
        self.assertEqual(parse_backouts(
            b'Backout b8601df335c1 (Bug 1174857) for bustage'),
            ([b'b8601df335c1'], [1174857]))

    def test_backout_multiple_changesets(self):
        # b'and' separated
        self.assertEqual(parse_backouts(
            b'Backed out changesets 4b6aa5c0a1bf and fdf38a41d92b (bug 1150549) for Mulet crashes.'),
            ([b'4b6aa5c0a1bf', b'fdf38a41d92b'], [1150549]))

        # more than two
        self.assertEqual(parse_backouts(
            b'Backed out changesets a8abdd77a92c, dda84d1fb12b and 21fdf73bbb17 (bug 1302907) for Windows build bustage'),
            ([b'a8abdd77a92c', b'dda84d1fb12b', b'21fdf73bbb17'], [1302907]))

        # oxford comma
        self.assertEqual(parse_backouts(
            b'Backed out changesets a8abdd77a92c, dda84d1fb12b, and 21fdf73bbb17 (bug 1302907) for Windows build bustage'),
            ([b'a8abdd77a92c', b'dda84d1fb12b', b'21fdf73bbb17'], [1302907]))

    def test_backout_n_changesets(self):
        # all nodes returned
        self.assertEqual(
            parse_backouts(
            b'Backed out 3 changesets (bug 1310885) for heap write hazard failures\n'
            b'Backed out changeset 77352010d8e8 (bug 1310885)\n'
            b'Backed out changeset 9245a2fbb974 (bug 1310885)\n'
            b'Backed out changeset 7c2db290c4b6 (bug 1310885)'),
            ([b'77352010d8e8', b'9245a2fbb974', b'7c2db290c4b6'], [1310885]))

        # nodes must be provided on following lines in strict mode
        self.assertIsNone(parse_backouts(
            b'Backed out 2 changesets (bug 1335751) for mochitest devtools failures',
            strict=True))

        # .. but is ok without strict mode
        self.assertEqual(parse_backouts(
            b'Backed out 2 changesets (bug 1335751) for mochitest devtools failures',
            strict=False),
            ([], [1335751]))

        # .. default should be with strict disabled
        self.assertEqual(parse_backouts(
            b'Backed out 2 changesets (bug 1335751) for mochitest devtools failures'),
            ([], [1335751]))

        # the correct number of nodes must be provided in strict mode
        self.assertIsNone(parse_backouts(
            b'Backed out 2 changesets (bug 1360992) for a 70% failure rate in test_fileReader.html on ASan e10s\n'
            b'Backed out changeset ab9fdee3a6a4 (bug 1360992)',
            strict=True))

        # .. but is ok without strict mode
        self.assertEqual(parse_backouts(
            b'Backed out 2 changesets (bug 1360992) for a 70% failure rate in test_fileReader.html on ASan e10s\n'
            b'Backed out changeset ab9fdee3a6a4 (bug 1360992)'),
            ([b'ab9fdee3a6a4'], [1360992]))

    def test_strip_commit_metadata(self):
        self.assertEqual(strip_commit_metadata(b'foo'), b'foo')

        self.assertEqual(strip_commit_metadata(b'foo\n\nbar'), b'foo\n\nbar')

        self.assertEqual(strip_commit_metadata(
            b'Bug 1 - foo\n\nMozReview-Commit-ID: abcdef'),
            b'Bug 1 - foo')

        self.assertEqual(strip_commit_metadata(
            b'Bug 1 - foo\n\nMore description\n\nFoo-Bar: baz\n\n'),
            b'Bug 1 - foo\n\nMore description\n\nFoo-Bar: baz')

        self.assertEqual(strip_commit_metadata(
            b'Bug 1 - foo\n\nMozReview-Commit-ID: abcdef\n\nTrailing desc'),
            b'Bug 1 - foo\n\n\nTrailing desc')


    def test_parse_commit_id(self):
        self.assertIsNone(parse_commit_id(b'foo'))
        self.assertIsNone(parse_commit_id(b'foo\n\nMozReview-Commit-ID\nbar'))

        self.assertEqual(parse_commit_id(b'MozReview-Commit-ID: foo123'),
                         b'foo123')
        self.assertEqual(parse_commit_id(
            b'Bug 1 - foo\n\nMozReview-Commit-ID: abc456'),
            b'abc456')


class TestAddHyperlinks(unittest.TestCase):
    def test_link_source_repo(self):
        self.assertEqual(add_hyperlinks(
            b'Source-Repo: not a link\n'),
            b'Source-Repo: not a link\n')

        self.assertEqual(add_hyperlinks(
            b'Source-Repo: https://example.com\n'),
            b'Source-Repo: <a href="https://example.com">https://example.com</a>\n')

        # On subsequent line
        self.assertEqual(add_hyperlinks(
            b'summary\n\nSource-Repo: https://example.com\n'),
            b'summary\n\nSource-Repo: <a href="https://example.com">https://example.com</a>\n')

        # With postfix content.
        self.assertEqual(add_hyperlinks(
            b'summary\n\nSource-Repo: https://example.com\nnext line\n'),
            b'summary\n\nSource-Repo: <a href="https://example.com">https://example.com</a>\nnext line\n')

        self.assertEqual(add_hyperlinks(
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

        # Check against malicious character in commit message.
        self.assertEqual(add_hyperlinks(
            b'Source-Repo: https://example.com?bad&escape=%20\n'),
            b'Source-Repo: <a href="https://example.com?bad&amp;escape=%20">https://example.com?bad&amp;escape=%20</a>\n')

    def test_link_revision(self):
        # GitHub revision is linked.
        self.assertEqual(add_hyperlinks(
            b'Source-Repo: https://github.com/mozilla/foo\n'
            b'Source-Revision: abcdef\n'),
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n'
            b'Source-Revision: <a href="https://github.com/mozilla/foo/commit/abcdef">abcdef</a>\n')

        # Non-GitHub revision isn't linked.
        self.assertEqual(add_hyperlinks(
            b'summary\n\n'
            b'Source-Repo: https://example.com/foo\n'
            b'Source-Revision: abcdef\n'),
            b'summary\n\n'
            b'Source-Repo: <a href="https://example.com/foo">https://example.com/foo</a>\n'
            b'Source-Revision: abcdef\n')

        # Bad characters in revision string are escaped.
        self.assertEqual(add_hyperlinks(
            b'Source-Repo: https://github.com/mozilla/foo\n'
            b'Source-Revision: a?b&c=%20\n'),
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n'
            b'Source-Revision: <a href="https://github.com/mozilla/foo/commit/a?b&amp;c=%20">a?b&amp;c=%20</a>\n')

    def test_link_github_issues(self):
        # "#\d+" in messages referencing a source GitHub repo should get linked
        # to GitHub issues.
        self.assertEqual(add_hyperlinks(
            b'Merge #5\n\n'
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'Merge <a href="https://github.com/mozilla/foo/issues/5">#5</a>\n\n'
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

        self.assertEqual(add_hyperlinks(
            b'Fix #34252\n\n'
            b'Related to PR #1321\n\n'
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'Fix <a href="https://github.com/mozilla/foo/issues/34252">#34252</a>\n\n'
            b'Related to PR <a href="https://github.com/mozilla/foo/issues/1321">#1321</a>\n\n'
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

        # "#string" isn't linked.
        self.assertEqual(add_hyperlinks(
            b'Merge #foo\n\n'
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'Merge #foo\n\n'
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

    def test_link_bugzilla(self):
        # Aggressive bug detection works normally.
        self.assertEqual(add_hyperlinks(
            b' 1234567\nfoo\n'),
            b' <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1234567">1234567</a>\nfoo\n')
        self.assertEqual(add_hyperlinks(
            b'bug 1\n'),
            b'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1">bug 1</a>\n')
        self.assertEqual(add_hyperlinks(
            b'bug 123456\n'),
            b'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">bug 123456</a>\n')
        self.assertEqual(add_hyperlinks(
            b'12345 is a bug\n'),
            b'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=12345">12345</a> is a bug\n')
        self.assertEqual(add_hyperlinks(
            b'foo #123456\n'),
            b'foo #<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">123456</a>\n')

        # When GitHub is in play, bare numbers are not hyperlinked and #\d is
        # for GitHub issues.

        self.assertEqual(add_hyperlinks(
            b'Bug 123456 - Fix all of the things\n\n'
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">Bug 123456</a> - Fix all of the things\n\n'
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

        self.assertEqual(add_hyperlinks(
            b'Merge #4256\n\n'
            b'This fixes #9000 and bug 324521\n\n'
            b'Source-Repo: https://github.com/mozilla/foo\n'),
            b'Merge <a href="https://github.com/mozilla/foo/issues/4256">#4256</a>\n\n'
            b'This fixes <a href="https://github.com/mozilla/foo/issues/9000">#9000</a> and '
            b'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=324521">bug 324521</a>\n\n'
            b'Source-Repo: <a href="https://github.com/mozilla/foo">https://github.com/mozilla/foo</a>\n')

    def test_link_xchannel(self):
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Active-Revision: a1234567890123456789'),
            b'X-Channel-Active-Revision: a1234567890123456789')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Revision: a1234567890123456789'),
            b'X-Channel-Revision: a1234567890123456789')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Revision: a1234567890123456789'),
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Revision: a1234567890123456789')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Converted-Revision: a1234567890123456789'),
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Converted-Revision: '
            b'<a href="https://hg.mozilla.org/mozilla-central/rev/a1234567890123456789">a1234567890123456789</a>')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Repo: releases/mozilla-esr-59_0.1\n'
            b'X-Channel-Converted-Revision: a1234567890123456789'),
            b'X-Channel-Repo: releases/mozilla-esr-59_0.1\n'
            b'X-Channel-Converted-Revision: '
            b'<a href="https://hg.mozilla.org/releases/mozilla-esr-59_0.1/rev/a1234567890123456789">a1234567890123456789</a>')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Revision: b1234567890123456789\n'
            b'X-Channel-Repo: releases/mozilla-beta\n'
            b'X-Channel-Converted-Revision: a1234567890123456789'),
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Revision: b1234567890123456789\n'
            b'X-Channel-Repo: releases/mozilla-beta\n'
            b'X-Channel-Converted-Revision: '
            b'<a href="https://hg.mozilla.org/releases/mozilla-beta/rev/a1234567890123456789">a1234567890123456789</a>')
        self.assertEqual(add_hyperlinks(
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Converted-Revision: b1234567890123456789\n'
            b'X-Channel-Repo: releases/mozilla-beta\n'
            b'X-Channel-Revision: a1234567890123456789'),
            b'X-Channel-Repo: mozilla-central\n'
            b'X-Channel-Converted-Revision: '
            b'<a href="https://hg.mozilla.org/mozilla-central/rev/b1234567890123456789">b1234567890123456789</a>\n'
            b'X-Channel-Repo: releases/mozilla-beta\n'
            b'X-Channel-Revision: a1234567890123456789')
        # try html through |escape|mozlink
        self.assertEqual(add_hyperlinks(htmlescape(
            b'X-Channel-Repo: mozilla-&\n'
            b'X-Channel-Revision: a1234567890123456789')),
            b'X-Channel-Repo: mozilla-&amp;\n'
            b'X-Channel-Revision: a1234567890123456789')

    def test_link_phabricator(self):
        """Tests hyperlinking of Phabricator URLs on hg.mozilla.org.
        Only support hyperlinking for URLs added to commit messages via
        the Lando API."""
        # Phabricator URL matching Lando insertion should be hyperlinked
        self.assertEqual(add_hyperlinks(
            b'Differential Revision: https://phabricator.services.mozilla.com/D1234'),
            b'Differential Revision: <a href="https://phabricator.services.mozilla.com/D1234">https://phabricator.services.mozilla.com/D1234</a>'
        )
