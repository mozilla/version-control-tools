# To enable:
#
# [extensions]
# buglink = /path/to/buglink.py

import re
from mercurial import templatefilters

bugzilla = r'<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=\2">\1</a>'
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
                        (?:\s*\#?)(\d+)
                     )''', re.I | re.X)

def buglink(x):
    return bug_re.sub(bugzilla, x)

templatefilters.filters["buglink"] = buglink

if __name__ == '__main__':
    import unittest
    
    _tests = (
        ('bug 1', ('', 'bug 1', '1', '')),
        ('bug 123456', ('', 'bug 123456', '123456', '')),
        ('testb=1234x', ('test', 'b=1234', '1234', 'x')),
        ('ab4665521e2f', None),
        ('Aug 2008', None),
        ('b=#12345', ('', 'b=#12345', '12345', '')),
        ('GECKO_191a2_20080815_RELBRANCH', None),
        ('12345 is a bug', ('', '12345', '12345', ' is a bug')),
        (' 123456 whitespace!', (' ', '123456', '123456', ' whitespace!')),
        )

    class TestBugRe(unittest.TestCase):
        def testreplacements(self):
            for str, result in _tests:
                if result is None:
                    resulttext = str
                else:
                    pretext, text, bugid, posttext = result
                    resulttext = '%s<a href="https://bugzilla.mozilla.org/show_bug.cgi?id=%s">%s</a>%s' % (pretext, bugid, text, posttext)

                self.assertEqual(resulttext, buglink(str))

    

    unittest.main()
