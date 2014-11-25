#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Script to perform an HTTP request.

from __future__ import print_function

import httplib
import sys
import urlparse
from argparse import ArgumentParser

def main(args):
    parser = ArgumentParser()
    parser.add_argument('--body-file',
        help='save HTTP response body to a file')
    parser.add_argument('--no-body', action='store_true',
        help='Do not print HTTP response body.')
    parser.add_argument('--header', action='append', default=[],
        help='Display only headers in this list. Values can be comma delimited.')
    parser.add_argument('--no-headers', action='store_true',
        help='Do not display any header info.')
    parser.add_argument('url',
        help='URL to fetch')

    args = parser.parse_args(args)
    url = args.url

    all_headers = not args.header
    display_headers = set()
    for header in args.header:
        display_headers |= set(header.split(','))

    url = urlparse.urlparse(url)

    conn = httplib.HTTPConnection(url.hostname, url.port or 80)
    path = url.path
    if url.query:
        path = '%s?%s' % (path, url.query)
    conn.request('GET', path)
    response = conn.getresponse()
    print(response.status)

    for header, value in response.getheaders():
        if not args.no_headers and (all_headers or header in display_headers):
            print('%s: %s' % (header, value))

    data = response.read()
    if args.body_file:
        with open(args.body_file, 'wb') as fh:
            fh.write(data)
    elif not args.no_body:
        print('')
        print(data)

sys.exit(main(sys.argv[1:]))
