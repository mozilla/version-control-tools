# To enable:
#
# [extensions]
# buglink = /path/to/buglink.py

import re
from mercurial import templatefilters

testedwith = '3.7 3.8 3.9 4.0'

bug_re = re.compile(r'''# bug followed by any sequence of numbers, or
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

bugzilla_link_templ = r'<a href="%s\2">\1</a>'
bugzilla_link = ""
bugzilla = "https://bugzilla.mozilla.org/show_bug.cgi?id="


def buglink(x):
    return bug_re.sub(bugzilla_link, x)

templatefilters.filters["buglink"] = buglink

def reposetup(ui, repo):
    global bugzilla
    global bugzilla_link
    bugzilla = ui.config("buglink", "bugzilla", bugzilla)
    bugzilla_link = bugzilla_link_templ % bugzilla
