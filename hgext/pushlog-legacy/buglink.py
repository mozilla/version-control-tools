# To enable:
#
# [extensions]
# buglink = /path/to/buglink.py

import re
from mercurial import templatefilters

bugzilla = r'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1</a>'
bug_re = re.compile(r'((?:bug|b=|(?=#?\d{4,}))(?:\s*#?)(\d+))', re.I)

def buglink(x):
    return bug_re.sub(bugzilla, x)

templatefilters.filters["buglink"] = buglink
