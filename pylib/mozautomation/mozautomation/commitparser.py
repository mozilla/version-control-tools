# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This module contains utilities for parsing commit messages.

import re

# These regular expressions are not very robust. Specifically, they fail to
# handle lists well.

BUG_RE = re.compile(
    br'''# bug followed by any sequence of numbers, or
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

# Like BUG_RE except it doesn't flag sequences of numbers, only positive
# "bug" syntax like "bug X" or "b=".
BUG_CONSERVATIVE_RE = re.compile(
    br'''((?:bug|b=)(?:\s*)(\d+)(?=\b))''', re.I | re.X)

SPECIFIER = br'(?:r|a|sr|rs|ui-r)[=?]'
R_SPECIFIER = br'\br[=?]'
R_SPECIFIER_RE = re.compile(R_SPECIFIER)
REQUAL_SPECIFIER_RE = re.compile(br'r=')
RQUESTION_SPECIFIER_RE = re.compile(br'r\?')

LIST = br'[;,\/\\]\s*'
LIST_RE = re.compile(LIST)

# Note that we only allows a subset of legal IRC-nick characters.
# Specifically we not allow [ \ ] ^ ` { | }
IRC_NICK = br'[a-zA-Z0-9\-\_.]*[a-zA-Z0-9\-\_]+'  # this needs to match irc nicks
BMO_IRC_NICK_RE = re.compile(br':(' + IRC_NICK + br')')

REVIEWERS_RE = re.compile(
    br'([\s\(\.\[;,])' +                 # before 'r' delimiter
    br'(' + SPECIFIER + br')' +           # flag
    br'(' +                              # capture all reviewers
        IRC_NICK +                      # reviewer
        br'(?:' +                        # additional reviewers
            LIST +                      # delimiter
            br'(?![a-z0-9\.\-]+[=?])' +  # don't extend match into next flag
            IRC_NICK +                  # reviewer
        br')*' +
    br')?')                              # noqa

BACKOUT_KEYWORD = br'^(?:backed out|backout|back out)\b'
BACKOUT_KEYWORD_RE = re.compile(BACKOUT_KEYWORD, re.I)
CHANGESET_KEYWORD = br'(?:\b(?:changeset|revision|change|cset|of)\b)'
CHANGESETS_KEYWORD = br'(?:\b(?:changesets|revisions|changes|csets|of)\b)'
SHORT_NODE = br'([0-9a-f]{12}\b)'
SHORT_NODE_RE = re.compile(SHORT_NODE, re.I)

BACKOUT_SINGLE_RE = re.compile(
    BACKOUT_KEYWORD + br'\s+' +
    CHANGESET_KEYWORD + br'?\s*' +
    br'(?P<node>' + SHORT_NODE + br')',
    re.I
)

BACKOUT_MULTI_SPLIT_RE = re.compile(
    BACKOUT_KEYWORD + br'\s+' +
    br'(?P<count>\d+)\s+' +
    CHANGESETS_KEYWORD,
    re.I
)

BACKOUT_MULTI_ONELINE_RE = re.compile(
    BACKOUT_KEYWORD + br'\s+' +
    CHANGESETS_KEYWORD + br'?\s*' +
    br'(?P<nodes>(?:(?:\s+|and|,)+' + SHORT_NODE + br')+)',
    re.I
)

SHORT_RE = re.compile(b'^[0-9a-f]{12}$', re.I)

DIGIT_RE = re.compile(b'#?\d+')

# Strip out a white-list of metadata prefixes.
# Currently just MozReview-Commit-ID
METADATA_RE = re.compile(b'^MozReview-Commit-ID: ')

DIFFERENTIAL_REVISION_RE = re.compile(br'(?P<phaburl>https://phabricator.services.mozilla.com/D\d+)')


def parse_bugs(s):
    is_github_repo = False
    m = RE_SOURCE_REPO.search(s)
    if m:
        source_repo = m.group(1)

        if source_repo.startswith(b'https://github.com/'):
            is_github_repo = True

    bugzilla_re = BUG_CONSERVATIVE_RE if is_github_repo else BUG_RE

    bugs_with_duplicates = [int(m[1]) for m in bugzilla_re.findall(s)]
    bugs_seen = set()
    bugs_seen_add = bugs_seen.add
    bugs = [x for x in bugs_with_duplicates if not (x in bugs_seen or bugs_seen_add(x))]
    return [bug for bug in bugs if bug < 100000000]


def filter_reviewers(s):
    """Given a string, extract meaningful reviewer names."""
    for word in s.strip().split():
        if not word:
            continue

        word = word.strip(b'"[]<>.:')

        if b'=' in word:
            continue

        if word.startswith(b'(') or word.endswith(b')'):
            continue

        if word == b'DONTBUILD':
            continue

        if DIGIT_RE.match(word):
            continue

        yield word


def parse_reviewers(commit_description, flag_re=None):
    if commit_description == '':
        return

    commit_summary = commit_description.splitlines().pop(0)
    for match in re.finditer(REVIEWERS_RE, commit_summary):
        if not match.group(3):
            continue

        for reviewer in re.split(LIST_RE, match.group(3)):
            if flag_re is None:
                yield reviewer
            elif flag_re.match(match.group(2)):
                yield reviewer


def parse_requal_reviewers(commit_description):
    for reviewer in parse_reviewers(commit_description,
                                    flag_re=REQUAL_SPECIFIER_RE):
        yield reviewer


def parse_rquestion_reviewers(commit_description):
    for reviewer in parse_reviewers(commit_description,
                                    flag_re=RQUESTION_SPECIFIER_RE):
        yield reviewer


def replace_reviewers(commit_description, reviewers):
    if not reviewers:
        reviewers_str = b''
    else:
        reviewers_str = b'r=' + b','.join(reviewers)

    if commit_description == b'':
        return reviewers_str

    commit_description = commit_description.splitlines()
    commit_summary = commit_description.pop(0)
    commit_description = b'\n'.join(commit_description)

    if not R_SPECIFIER_RE.search(commit_summary):
        commit_summary += b' ' + reviewers_str
    else:
        # replace the first r? with the reviewer list, and all subsequent
        # occurences with a marker to mark the blocks we need to remove
        # later
        d = {b'first': True}

        def replace_first_reviewer(matchobj):
            if R_SPECIFIER_RE.match(matchobj.group(2)):
                if d[b'first']:
                    d[b'first'] = False
                    return matchobj.group(1) + reviewers_str
                else:
                    return b'\0'
            else:
                return matchobj.group(0)

        commit_summary = re.sub(REVIEWERS_RE, replace_first_reviewer,
                                commit_summary)

        # remove marker values as well as leading separators.  this allows us
        # to remove runs of multiple reviewers and retain the trailing
        # separator.
        commit_summary = re.sub(LIST + b'\0', b'', commit_summary)
        commit_summary = re.sub(b'\0', b'', commit_summary)

    if commit_description == b"":
        return commit_summary.strip()
    else:
        return commit_summary.strip() + b"\n" + commit_description


def is_backout(commit_desc):
    """Returns True if the first line of the commit description appears to
    contain a backout.

    Backout commits should always result in is_backout() returning True,
    and parse_backouts() not returning None.  Malformed backouts may return
    True here and None from parse_backouts()."""
    return BACKOUT_KEYWORD_RE.match(commit_desc) is not None


def parse_backouts(commit_desc, strict=False):
    """Look for backout annotations in a string.

    Returns a 2-tuple of (nodes, bugs) where each entry is an iterable of
    changeset identifiers and bug numbers that were backed out, respectively.
    Or return None if no backout info is available.

    Setting `strict` to True will enable stricter validation of the commit
    description (eg. ensuring N commits are provided when given N commits are
    being backed out).
    """
    if not is_backout(commit_desc):
        return None

    lines = commit_desc.splitlines()
    first_line = lines[0]

    # Single backout.
    m = BACKOUT_SINGLE_RE.match(first_line)
    if m:
        return [m.group('node')], parse_bugs(first_line)

    # Multiple backouts, with nodes listed in commit description.
    m = BACKOUT_MULTI_SPLIT_RE.match(first_line)
    if m:
        expected = int(m.group('count'))
        nodes = []
        for line in lines[1:]:
            single_m = BACKOUT_SINGLE_RE.match(line)
            if single_m:
                nodes.append(single_m.group('node'))
        if strict:
            # The correct number of nodes must be specified.
            if expected != len(nodes):
                return None
        return nodes, parse_bugs(commit_desc)

    # Multiple backouts, with nodes listed on the first line
    m = BACKOUT_MULTI_ONELINE_RE.match(first_line)
    if m:
        return SHORT_NODE_RE.findall(m.group('nodes')), parse_bugs(first_line)

    return None


def strip_commit_metadata(s):
    """Strips metadata related to commit tracking.

    Will strip lines like "MozReview-Commit-ID: foo" from the commit
    message.
    """
    # TODO this parsing is overly simplied. There is room to handle
    # empty lines before the metadata.
    lines = [l for l in s.splitlines() if not METADATA_RE.match(l)]

    while lines and not lines[-1].strip():
        lines.pop(-1)

    if type(s) == str:
        joiner = b'\n'
    elif type(s) == unicode:
        joiner = u'\n'
    else:
        raise TypeError('do not know type of commit message: %s' % type(s))

    return joiner.join(lines)


def parse_commit_id(s):
    """Parse a MozReview-Commit-ID value out of a string.

    Returns None if the commit ID is not found.
    """
    m = re.search(b'^MozReview-Commit-ID: ([a-zA-Z0-9]+)$', s, re.MULTILINE)
    if not m:
        return None

    return m.group(1)


RE_SOURCE_REPO = re.compile(b'^Source-Repo: (https?:\/\/.*)$',
                            re.MULTILINE)
RE_SOURCE_REVISION = re.compile(b'^Source-Revision: (.*)$', re.MULTILINE)

RE_XCHANNEL_REVISION = re.compile(
    b'^X-Channel-Repo: (?P<repo>[a-zA-Z0-9/\-._]+?)\n'
    b'X-Channel-Converted-Revision: (?P<revision>[a-fA-F0-9]{12,40}?)$',
    re.MULTILINE)


def xchannel_link(m):
    s = m.group()[:(m.start('revision') - m.start())]
    l = b'<a href="https://hg.mozilla.org/%(repo)s/rev/%(revision)s">%(revision)s</a>'
    s += l % {
        b'repo': m.group('repo'),
        b'revision': m.group('revision'),
    }
    s += m.group()[(m.end('revision') - m.start()):]
    return s


def differential_revision_repl(match):
    """Replacement function to linkify Phabricator Differential
    Revision URLs in commit messages."""
    phaburl = match.group('phaburl')
    return b'<a href="%(link)s">%(link)s</a>' % {b'link': phaburl}


def htmlescape(s, quote=None):
    '''Replace special characters "&", "<" and ">" to HTML-safe sequences.
    If the optional flag quote is true, the quotation mark character (")
    is also translated.

    This is the same as cgi.escape in Python, but always operates on
    bytes, whereas cgi.escape in Python 3 only works on unicodes.
    '''
    s = s.replace(b"&", b"&amp;")
    s = s.replace(b"<", b"&lt;")
    s = s.replace(b">", b"&gt;")
    if quote:
        s = s.replace(b'"', b"&quot;")
    return s


def add_hyperlinks(s,
                   bugzilla_url=b'https://bugzilla.mozilla.org/show_bug.cgi?id='):
    """Add hyperlinks to a commit message.

    This is useful to be used as a Mercurial template filter for converting
    plain text into rich HTML.
    """
    # Look for annotations saying this commit originally came from elsewhere.
    # If these are present, we are less aggressive about e.g. linking numbers
    # to Bugzilla bugs.
    source_repo = None
    github_repo = None

    m = RE_SOURCE_REPO.search(s)
    if m:
        source_repo = m.group(1)

        if source_repo.startswith(b'https://github.com/'):
            github_repo = source_repo[len(b'https://github.com/'):]

        start, end = m.span(1)

        s = b'%s<a href="%s">%s</a>%s' % (
            s[0:start],
            htmlescape(source_repo),
            htmlescape(source_repo),
            s[end:])

    m = RE_SOURCE_REVISION.search(s)
    if m:
        source_revision = m.group(1)

        start, end = m.span(1)

        # Hyperlink to GitHub commits.
        if github_repo:
            s = b'%s<a href="https://github.com/%s/commit/%s">%s</a>%s' % (
                s[0:start],
                htmlescape(github_repo),
                htmlescape(source_revision),
                htmlescape(source_revision),
                s[end:])

    # We replace #\d+ with links to the GitHub issue.
    if github_repo:
        repl = br'<a href="https://github.com/%s/issues/\1">#\1</a>' % github_repo
        s = re.sub(br'#(\d+)', repl, s)

    # Bugzilla linking.
    bugzilla_re = BUG_CONSERVATIVE_RE if github_repo else BUG_RE
    bugzilla_link = br'<a href="%s\2">\1</a>' % bugzilla_url
    s = bugzilla_re.sub(bugzilla_link, s)

    # l10n cross channel linking
    s = RE_XCHANNEL_REVISION.sub(xchannel_link, s)

    # Linkify Phabricator differentials
    s = DIFFERENTIAL_REVISION_RE.sub(differential_revision_repl, s)

    return s
