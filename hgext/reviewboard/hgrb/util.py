# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import errno
import random
import re
import time

from mercurial import (
    error,
    util,
)
from mercurial.i18n import _

class ReviewID(object):
    """Represents a parsed review identifier."""

    def __init__(self, rid):
        self.bug = None
        self.user = None

        if not rid:
            return

        # Assume digits are Bugzilla bugs.
        if rid.isdigit():
            rid = 'bz://%s' % rid

        if rid and not rid.startswith('bz://'):
            raise error.Abort(_('review identifier must begin with bz://'))

        full = rid
        paths = rid[5:].split('/')
        if not paths[0]:
            raise error.Abort(_('review identifier must not be bz://'))

        bug = paths[0]
        if not bug.isdigit():
            raise error.Abort(_('first path component of review identifier '
                                'must be a bug number'))
        self.bug = int(bug)

        if bug == 0:
            raise error.Abort(_('bug number must not be zero'))

        if len(paths) > 1:
            self.user = paths[1]

        if len(paths) > 2:
            raise error.Abort(_('unrecognized review id: %s') % rid)

    def __nonzero__(self):
        if self.bug or self.user:
            return True

        return False

    @property
    def full(self):
        s = 'bz://%s' % self.bug
        if self.user:
            s += '/%s' % self.user

        return s


BASE62_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# (datetime.datetime(2000, 1, 1, 0, 0, 0, 0) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
EPOCH = 946684800

def genid(repo=None, fakeidpath=None):
    """Generate a unique identifier.

    Unique identifiers are treated as a black box. But under the hood, they
    consist of a time component and a random component.

    Each identifier is up to 64 bits. The first 32 bits are random. The
    final 32 bits are integer seconds since midnight UTC on January 1, 2000. We
    don't use UNIX epoch because dates from the 70's aren't interesting to us.

    The birthday paradox says we only need sqrt() attempts before we generate
    a collision. So for 32 bits, we need 2^16 or 65,536 generations on average
    before there is a collision. We estimate there will be a commit every 10s
    for the Firefox repo. The chance of a collision should be very small.

    Base62 is used as the encoding mechanism because it is safe for both
    URLs and revsets. We could get base66 for URLs, but the characters
    -~. could conflict with revsets.
    """
    # Provide a backdoor to generate deterministic IDs. This is used for
    # testing purposes because tests want constant output. And since
    # commit IDs go into the commit and are part of the SHA-1, they need
    # to be deterministic.
    if repo and repo.ui.configbool('reviewboard', 'fakeids', False):
        fakeidpath = repo.vfs.join('genid')

    if fakeidpath:
        try:
            with open(fakeidpath, 'rb') as fh:
                data = fh.read()
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

            data = None

        if data:
            n = int(data)
        else:
            n = 0

        seconds = EPOCH
        rnd = n
        with open(fakeidpath, 'wb') as fh:
            fh.write(str(n + 1))
    else:
        now = int(time.time())
        # May 5, 2015 sometime.
        if now < 1430860700:
            raise error.Abort('your system clock is wrong; fix your system '
                              'clock')
        seconds = now - EPOCH
        rnd = random.SystemRandom().getrandbits(32)

    value = (rnd << 32) + seconds

    chars = []
    while value > 0:
        quot, remain = divmod(value, 62)
        chars.append(BASE62_CHARS[remain])
        value = quot

    return ''.join(reversed(chars))


def addcommitid(msg, repo=None, fakeidpath=None):
    """Add a commit ID to a commit message."""
    lines = msg.splitlines()

    # Prune blank lines at the end.
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return msg, False

    if any(l.startswith('MozReview-Commit-ID: ') for l in lines):
        return msg, False

    # Insert empty line between main commit message and metadata.
    # Metadata lines are have-defined keys and values not containing
    # whitespaces.
    if not re.match('^[a-zA-Z-]+: \S+$', lines[-1]) or len(lines) == 1:
        lines.append('')

    cid = genid(repo=repo, fakeidpath=fakeidpath)
    lines.append('MozReview-Commit-ID: %s' % cid)

    return '\n'.join(lines), True

def reencoderesponseinplace(response):
    """
    tuple is not handled by now.
    """
    def dicthandler(dictresponse):
        for k, v in dictresponse.items():
            nk = k.encode('utf-8') if isinstance(k, unicode) else k
            dictresponse[nk] = dictresponse.pop(k)

            if isinstance(v, unicode):
                dictresponse[nk] = v.encode('utf-8')
            else:
                reencoderesponseinplace(v)

    def listhandler(listresponse):
        for idx in xrange(len(listresponse)):
            if isinstance(listresponse[idx], unicode):
                listresponse[idx] = listresponse[idx].encode('utf-8')
            else:
                reencoderesponseinplace(listresponse[idx])

    if isinstance(response, dict):
        dicthandler(response)
    elif isinstance(response, list):
        listhandler(response)
