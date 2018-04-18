# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import collections
from mercurial import util
from mercurial.node import short
from mozautomation.commitparser import (
    parse_requal_reviewers,
    is_backout,
)

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
    print_notice,
)

DOM_PEERS = [
    dict(name='Andrea Marchesini', nick=['baku'], email=['amarchesini@mozilla.com']),
    dict(name='Andrew McCreight', nick=['mccr8'], email=['continuation@gmail.com']),
    dict(name='Ben Kelly', nick=['bkelly'], email=['bkelly@mozilla.com', 'ben@wanderview.com']),
    dict(name='Blake Kaplan', nick=['mrbkap'], email=['mrbkap@gmail.com']),
    dict(name='Bobby Holley', nick=['bholley'], email=['bholley@mozilla.com']),
    dict(name='Boris Zbarsky', nick=['bz', 'bzbarsky'], email=['bzbarsky@mit.edu']),
    dict(name='Ehsan Akhgari', nick=['ehsan'], email=['ehsan@mozilla.com', 'ehsan.akhgari@gmail.com']),
    dict(name='Henri Sivonen', nick=['hsivonen'], email=['hsivonen@hsivonen.fi']),
    dict(name='Kyle Machulis', nick=['qdot', 'kmachulis'], email=['qdot@mozilla.com', 'kmachulis@mozilla.com', 'kyle@nonpolynomial.com']),
    dict(name='Nika Layzell', nick=['mystor'], email=['nika@thelayzells.com']),
    dict(name='Olli Pettay', nick=['smaug'], email=['olli.pettay@helsinki.fi', 'bugs@pettay.fi']),
    dict(name='Peter Van der Beken', nick=['peterv'], email=['peterv@propagandism.org']),
]

# The root directory for WebIDL files which contain only ChromeOnly
# interfaces, and do not require DOM peer review.
CHROME_WEBIDL_ROOT = 'dom/chrome-webidl/'

# Servo WebIDL files do not need DOM Peer review.
SERVO_ROOT = 'servo/'

MISSING_REVIEW = """
Changeset %s alters WebIDL file(s) without DOM peer review:
%s

Please, request review from either:
"""
for p in DOM_PEERS:
    MISSING_REVIEW += "  - {} (:{})\n".format(p['name'], p['nick'][0])

CHROME_ONLY = """
Not enforcing DOM peer review for WebIDL files within the chrome WebIDL root.
Please make sure changes do not contain any web-visible binding definitions.
"""

SERVO_ONLY = """
Not enforcing DOM peer review for WebIDL files within Servo.
Please make sure changes do not contain any web-visible binding definitions.
"""


class WebIDLCheck(PreTxnChangegroupCheck):
    """Prevents WebIDL file modifications without appropriate review."""
    @property
    def name(self):
        return 'webidl_check'

    def relevant(self):
        return self.repo_metadata['firefox_releasing']

    def pre(self, node):
        # Accept the entire push for code uplifts
        changesets = list(self.repo.changelog.revs(self.repo[node].rev()))
        self.is_uplift = 'a=release' in self.repo.changectx(
            changesets[-1]).description().lower()

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
        webidl_files = [f for f in ctx.files() if f.endswith('.webidl')]
        if not webidl_files:
            return True

        # Allow patches authored by peers
        if is_peer_email(util.email(ctx.user())):
            return True

        # Categorise files
        file_counts = collections.Counter()
        review_required_files = []
        for f in webidl_files:
            file_counts['total'] += 1
            if f.startswith(CHROME_WEBIDL_ROOT):
                file_counts['chrome'] += 1
            elif f.startswith(SERVO_ROOT):
                file_counts['servo'] += 1
            else:
                review_required_files.append(f)

        # Allow chrome-only and servo-only changes
        if file_counts['chrome'] + file_counts['servo'] == file_counts['total']:
            if file_counts['chrome']:
                print_notice(self.ui, CHROME_ONLY)
            if file_counts['servo']:
                print_notice(self.ui, SERVO_ONLY)
            return True

        # Allow if reviewed by any peer
        requal = list(parse_requal_reviewers(ctx.description()))
        if any(is_peer_nick(nick) for nick in requal):
            return True

        # Reject
        print_banner(self.ui, 'error',
                     MISSING_REVIEW % (short(ctx.node()),
                                       '\n'.join(review_required_files)))
        return False

    def post_check(self):
        return True


def is_peer_email(email):
    email = email.lower()
    for peer in DOM_PEERS:
        if email in peer['email']:
            return True
    return False


def is_peer_nick(nick):
    nick = nick.lower()
    for peer in DOM_PEERS:
        if nick in peer['nick']:
            return True
    return False
