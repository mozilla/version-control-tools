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
           (?:\s*\#?)(\d+)
         )''', re.I | re.X)

REVIEW_RE = re.compile(r'[ra][=?]+(\w[^ ]+)')

LIST_RE = re.compile(r'[;\.,\+\/\\]')

def parse_bugs(s):
    return [int(m[1]) for m in BUG_RE.findall(s)]

def parse_reviewers(s):
    for r in REVIEW_RE.findall(s):
        for part in LIST_RE.split(r):
            yield part.strip('[](){}')
