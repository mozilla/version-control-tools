from __future__ import absolute_import, print_function

import sys

def flush():
    sys.stdout.flush()
    sys.stderr.flush()

globalvars = {}
lines = sys.stdin.readlines()
while lines:
    l = lines.pop(0)
    if l.startswith('SALT'):
        print(l[:-1])
    elif l.startswith('>>> '):
        snippet = l[4:]
        while lines and lines[0].startswith('... '):
            l = lines.pop(0)
            snippet += l[4:]
        c = compile(snippet, '<heredoc>', 'single')
        try:
            flush()
            exec(c, globalvars)
            flush()
        except Exception as inst:
            flush()
            print(repr(inst))
