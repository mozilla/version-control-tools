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

SPECIFIER           = r'(?:r|a|sr|rs|ui-r)[=?]'
REQUAL_SPECIFIER_RE = re.compile(r'r=')
RQUESTION_SPECIFIER_RE = re.compile(r'r\?')

LIST    = r'[;,\/\\]\s*'
LIST_RE = re.compile(LIST)

REVIEWER = r'[a-zA-Z0-9\-\_]+'         # this needs to match irc nicks

REVIEWERS_RE = re.compile(
    r'([\s\(\.\[;,])' +                # before 'r' delimiter
    r'(' + SPECIFIER + r')' +          # flag
    r'(' +                             # capture all reviewers
        REVIEWER +                     # reviewer
        r'(?:' +                       # additional reviewers
            LIST +                     # delimiter
            r'(?![a-z0-9\.\-]+[=?])' + # don't extend match into next flag
            REVIEWER  +                # reviewer
        r')*' +
    r')')

BACKED_OUT_RE = re.compile('^backed out changeset (?P<node>[0-9a-f]{12}) ',
                           re.I)

BACKOUT_RE = re.compile('^back\s?out (?P<node>[0-9a-f]{12}) ', re.I)

SHORT_RE = re.compile('^[0-9a-f]{12}$', re.I)

DIGIT_RE = re.compile('#?\d+')

BACK_OUT_MULTIPLE_RE = re.compile(
    '^back(?:ed)? out \d+ changesets \(bug ', re.I)


def parse_bugs(s):
    bugs = [int(m[1]) for m in BUG_RE.findall(s)]
    return [bug for bug in bugs if bug < 100000000]


def filter_reviewers(s):
    """Given a string, extract meaningful reviewer names."""
    for word in s.strip().split():
        if not word:
            continue

        word = word.strip('"[]<>.:')

        if '=' in word:
            continue

        if word.startswith('(') or word.endswith(')'):
            continue

        if word == 'DONTBUILD':
            continue

        if DIGIT_RE.match(word):
            continue

        yield word


def parse_reviewers(commit_description, flag_re=None):
    commit_summary = commit_description.splitlines().pop(0)
    for match in re.finditer(REVIEWERS_RE, commit_summary):
        for reviewer in re.split(LIST_RE, match.group(3)):
            if flag_re == None:
                yield reviewer
            elif flag_re.match(match.group(2)):
                yield reviewer


def parse_requal_reviewers(commit_description):
    for reviewer in parse_reviewers(commit_description, flag_re=REQUAL_SPECIFIER_RE):
        yield reviewer


def parse_rquestion_reviewers(commit_description):
    for reviewer in parse_reviewers(commit_description, flag_re=RQUESTION_SPECIFIER_RE):
        yield reviewer


def parse_backouts(s):
    """Look for backout annotations in a string.

    Returns a 2-tuple of (nodes, bugs) where each entry is an iterable of
    changeset identifiers and bug numbers that were backed out, respectively.
    Or return None if no backout info is available.
    """
    l = s.splitlines()[0].lower()

    m = BACKED_OUT_RE.match(l)
    if m:
        return [m.group('node')], parse_bugs(s)

    m = BACKOUT_RE.match(l)
    if m:
        return [m.group('node')], parse_bugs(s)

    if BACK_OUT_MULTIPLE_RE.match(l):
        return [], parse_bugs(s)

    for prefix in ('backed out changesets ', 'back out changesets '):
        if l.startswith(prefix):
            nodes = []
            remaining = l[len(prefix):]

            # Consume all the node words that follow, stopping after a non-node
            # word or separator.
            for word in remaining.split():
                word = word.strip(',')
                if SHORT_RE.match(word):
                    nodes.append(word)
                elif word == 'and':
                    continue
                else:
                    break

            return nodes, parse_bugs(s)

    return None
