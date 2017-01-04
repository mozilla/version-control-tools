# To enable:
#
# [extensions]
# buglink = /path/to/buglink.py

import os
from mercurial import templatefilters

OUR_DIR = os.path.dirname(__file__)
ROOT = os.path.normpath(os.path.join(OUR_DIR, '..', '..'))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozautomation.commitparser import BUG_RE

testedwith = '3.7 3.8 3.9 4.0'

bugzilla_link_templ = r'<a href="%s\2">\1</a>'
bugzilla_link = ""
bugzilla = "https://bugzilla.mozilla.org/show_bug.cgi?id="


def buglink(x):
    return BUG_RE.sub(bugzilla_link, x)

templatefilters.filters["buglink"] = buglink

def reposetup(ui, repo):
    global bugzilla
    global bugzilla_link
    bugzilla = ui.config("buglink", "bugzilla", bugzilla)
    bugzilla_link = bugzilla_link_templ % bugzilla
