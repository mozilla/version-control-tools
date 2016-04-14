#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Continuosly run `hg unifyrepo`"""

import argparse
import os
import subprocess
import sys
import time

HERE = os.path.abspath(os.path.dirname(__file__))
UNIFYEXT = os.path.join(HERE, '__init__.py')


def unify_until_error(hg, configs, delay=30, maximum=0):
    i = 0
    while True:
        for config in configs:
            args = [
                hg, '--config', 'extensions.unifyrepo=%s' % UNIFYEXT,
                'unifyrepo', config
            ]
            res = subprocess.call(args)
            if res:
                return res

        time.sleep(delay)

        i += 1
        if maximum > 0 and i >= maximum:
            return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hg', help='path to hg executable to use')
    parser.add_argument('config', nargs='+', help='unify config files to use')
    parser.add_argument('--delay', type=int, default=30,
                        help='Delay in seconds between unify invocations')
    parser.add_argument('--maximum', type=int, default=0,
                        help='Maximum number of iterations to process')

    args = parser.parse_args()

    sys.exit(unify_until_error(args.hg, args.config, delay=args.delay,
                               maximum=args.maximum))
