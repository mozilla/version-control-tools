# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import collections
from mercurial.node import short
from mercurial.utils import stringutil
from mozautomation.commitparser import (
    parse_requal_reviewers,
    is_backout,
)
from mozhg.util import repo_owner

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
    print_notice,
)

DOM_PEERS = [
    {
        "name": b"Andrea Marchesini",
        "nick": [b"baku"],
        "email": [b"amarchesini@mozilla.com"],
    },
    {"name": b"Andreas Farre", "nick": [b"farre"], "email": [b"afarre@mozilla.com"]},
    {
        "name": b"Andrew McCreight",
        "nick": [b"mccr8"],
        "email": [b"continuation@gmail.com"],
    },
    {
        "name": b"Andrew Sutherland",
        "nick": [b"asuth"],
        "email": [b"bugmail@asutherland.org", b"asuth@mozilla.com"],
    },
    {"name": b"Bobby Holley", "nick": [b"bholley"], "email": [b"bholley@mozilla.com"]},
    {"name": b"Edgar Chen", "nick": [b"edgar"], "email": [b"echen@mozilla.com"]},
    {"name": b"Emilio Cobos", "nick": [b"emilio"], "email": [b"emilio@crisal.io"]},
    {
        "name": b"Henri Sivonen",
        "nick": [b"hsivonen"],
        "email": [b"hsivonen@hsivonen.fi"],
    },
    {
        "name": b"Kagami Rosylight",
        "nick": [b"saschanaz"],
        "email": [b"krosylight@mozilla.com"],
    },
    {
        "name": b"Nika Layzell",
        "nick": [b"mystor", b"nika"],
        "email": [b"nika@thelayzells.com"],
    },
    {
        "name": b"Olli Pettay",
        "nick": [b"smaug"],
        "email": [b"olli.pettay@helsinki.fi", b"bugs@pettay.fi"],
    },
    {"name": b"Sean Feng", "nick": [b"sefeng"], "email": [b"sefeng@mozilla.com"]},
]

# The root directory for WebIDL files which contain only ChromeOnly
# interfaces, and do not require DOM peer review.
CHROME_WEBIDL_ROOT = b"dom/chrome-webidl/"

# Bug 1941617 - typescript config doesn't require DOM peer review
TS_WEBIDL_ROOT = b"tools/ts/config/"

MISSING_REVIEW = b"""
Changeset %s alters WebIDL file(s) without DOM peer review:
%s

Please, request review from the #webidl reviewer group or either:
"""
for p in DOM_PEERS:
    MISSING_REVIEW += b"  - %s (:%s)\n" % (p["name"], p["nick"][0])

CHROME_ONLY = b"""
Not enforcing DOM peer review for WebIDL files within the chrome WebIDL root.
Please make sure changes do not contain any web-visible binding definitions.
"""


class WebIDLCheck(PreTxnChangegroupCheck):
    """Prevents WebIDL file modifications without appropriate review."""

    @property
    def name(self):
        return b"webidl_check"

    def relevant(self):
        return (
            self.repo_metadata[b"firefox_releasing"]
            and repo_owner(self.repo) != b"scm_allow_direct_push"
        )

    def pre(self, node):
        # Accept the entire push for code uplifts
        self.is_uplift = b"a=release" in self.repo[b"tip"].description().lower()

    def check(self, ctx):
        if self.is_uplift:
            return True

        # Ignore merge changesets
        if len(ctx.parents()) > 1:
            return True

        # Ignore backouts
        if is_backout(ctx.description()):
            return True

        # Ignore changes that don't touch .webidl files
        webidl_files = [f for f in ctx.files() if f.endswith(b".webidl")]
        if not webidl_files:
            return True

        # Allow patches authored by peers
        if is_peer_email(stringutil.email(ctx.user())):
            return True

        # Categorise files
        file_counts = collections.Counter()
        review_required_files = []
        for f in webidl_files:
            file_counts["total"] += 1
            if f.startswith(CHROME_WEBIDL_ROOT):
                file_counts["chrome"] += 1
            elif f.startswith(TS_WEBIDL_ROOT):
                file_counts["ts"] += 1
            else:
                review_required_files.append(f)

        # Allow chrome-only changes
        if not review_required_files:
            if file_counts["chrome"]:
                print_notice(self.ui, CHROME_ONLY)
            return True

        # Allow if reviewed by any peer
        requal = list(parse_requal_reviewers(ctx.description()))
        if any(is_peer_nick(nick) for nick in requal):
            return True

        # Reject
        print_banner(
            self.ui,
            b"error",
            MISSING_REVIEW % (short(ctx.node()), b"\n".join(review_required_files)),
        )
        return False

    def post_check(self):
        return True


def is_peer_email(email):
    email = email.lower()
    for peer in DOM_PEERS:
        if email in peer["email"]:
            return True
    return False


def is_peer_nick(nick):
    nick = nick.lower()
    for peer in DOM_PEERS:
        if nick in peer["nick"]:
            return True
    return False
