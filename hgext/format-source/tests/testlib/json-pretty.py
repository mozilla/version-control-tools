r"""Command-line tool to validate and pretty-print JSON

Usage::

    $ echo '{"json":"obj"}' | python -m json.tool
    {
        "json": "obj"
    }
    $ echo '{ 1.2:3.4}' | python -m json.tool
    Expecting property name enclosed in double quotes: line 1 column 3 (char 2)

"""
import os
import sys
import json

def main():
    if len(sys.argv) == 1:
        infile = sys.stdin
        outfile = sys.stdout
    elif len(sys.argv) == 2:
        infile = open(sys.argv[1], 'rb')
        outfile = sys.stdout
    elif len(sys.argv) == 3:
        infile = open(sys.argv[1], 'rb')
        outfile = open(sys.argv[2], 'wb')
    else:
        raise SystemExit(sys.argv[0] + " [infile [outfile]]")
    with infile:
        try:
            obj = json.load(infile)
        except ValueError, e:
            raise SystemExit(e)
    if os.path.exists('.json-indent'):
        indent = int(open('.json-indent').read())
    else:
        indent = 4
    with outfile:
        json.dump(obj, outfile, sort_keys=True,
                  indent=indent, separators=(',', ': '))
        outfile.write('\n')


if __name__ == '__main__':
    main()
