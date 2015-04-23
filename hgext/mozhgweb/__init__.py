# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Extensions to hgweb used by Mozilla."""

import os
from mercurial import templatefilters

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozautomation.commitparser import BUG_RE

RE_BUGZILLA_LINK = r'<a href="%s\2">\1</a>'
BUGZILLA_LINK = ''
BUGZILLA_URL = 'https://bugzilla.mozilla.org/show_bug.cgi?id='


def buglink(x):
    return BUG_RE.sub(BUGZILLA_LINK, x)


def reposetup(ui, repo):
    global BUGZILLA_URL
    global BUGZILLA_LINK
    BUGZILLA_URL = ui.config('buglink', 'bugzilla', BUGZILLA_URL)
    BUGZILLA_LINK = RE_BUGZILLA_LINK % BUGZILLA_URL


def extsetup(ui):
    templatefilters.filters['buglink'] = buglink
