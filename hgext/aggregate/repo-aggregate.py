#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Continuosly run `hg aggregate`

Ideally, the functionality provided by this script lives inside
`hg aggregate`. However, Mercurial has a history of leaking memory
attached to repository instances. This was encountered during the
development of this script, leading to the establishing of this
separate script.
"""

import optparse
import os
import subprocess
import sys
import time

HERE = os.path.abspath(os.path.dirname(__file__))
AGGREGATE = os.path.join(HERE, '__init__.py')

def run():
    parser = optparse.OptionParser()
    parser.add_option('--delay', type=int, default=30,
        help='Delay between aggregation runs')
    parser.add_option('--maximum', type=int, default=0,
        help='Maximum number of iterations to process')

    options, args = parser.parse_args()

    if len(args) != 2:
        print('usage: %s /path/to/hg /path/to/repo' % sys.argv[0])
        sys.exit(1)

    hg, repo = args

    sys.exit(aggregate_until_error(hg, repo, delay=options.delay,
        maximum=options.maximum))

def aggregate_once(hg, repo):
    args = [
        hg,
        '--config', 'extensions.aggregate=%s' % AGGREGATE,
        '-R', repo,
        'aggregate',
    ]
    return subprocess.call(args)

def aggregate_until_error(hg, repo, delay=30, maximum=0):
    i = 0
    while True:
        res = aggregate_once(hg, repo)
        if res:
            return res

        time.sleep(delay)

        i += 1
        if maximum > 0 and i >= maximum:
            return 0

if __name__ == '__main__':
    run()
