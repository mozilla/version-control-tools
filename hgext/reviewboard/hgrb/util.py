# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from mercurial import util
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
            raise util.Abort(_('review identifier must begin with bz://'))

        full = rid
        paths = rid[5:].split('/')
        if not paths[0]:
            raise util.Abort(_('review identifier must not be bz://'))

        bug = paths[0]
        if not bug.isdigit():
            raise util.Abort(_('first path component of review identifier must be a bug number'))
        self.bug = int(bug)

        if len(paths) > 1:
            self.user = paths[1]

        if len(paths) > 2:
            raise util.Abort(_('unrecognized review id: %s') % rid)

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
