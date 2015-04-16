# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This module contains utilities for parsing commit messages.

import re

# These regular expressions are not very robust. Specifically, they fail to
# handle lists well.

BUG_RE = re.compile(
    r'''# bug followed by any sequence of numbers, or
        # a standalone sequence of numbers
         (
           (?:
             bug |
             b= |
             # a sequence of 5+ numbers preceded by whitespace
             (?=\b\#?\d{5,}) |
             # numbers at the very beginning
             ^(?=\d)
           )
           (?:\s*\#?)(\d+)(?=\b)
         )''', re.I | re.X)

SPECIFIER_RE = re.compile(r'[ra][=?]')

REQUAL_SPECIFIER_RE = re.compile(r'r=')

LIST_RE = re.compile(r'[;\.,\/\\]')


def parse_bugs(s):
    bugs = [int(m[1]) for m in BUG_RE.findall(s)]
    return [bug for bug in bugs if bug < 100000000]

def parse_reviewers(s):
    for r in SPECIFIER_RE.split(s)[1:]:
        for part in LIST_RE.split(r):
            part = part.strip('[](){} ')
            if part:
                # strip off the 'specifier' if any
                yield SPECIFIER_RE.split(part)[-1]

def parse_requal_reviewers(s):
    for r in REQUAL_SPECIFIER_RE.split(s)[1:]:
        for part in LIST_RE.split(r):
            part = part.strip('[](){} ')
            if part:
                part = REQUAL_SPECIFIER_RE.split(part)[-1]
                # we've stripped off 'r=' but we might still have another
                # specifier
                if not SPECIFIER_RE.match(part):
                    yield part
