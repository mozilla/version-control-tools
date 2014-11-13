#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from optparse import OptionParser
import sys

def aggregate(fh, min_size=0):
    entries = {}

    for line in fh:
        parts = line.rstrip().split()

        when, repo, size, t_wall, t_cpu = parts
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        totals = entries.setdefault((when, repo), [0, 0.0, 0.0])
        totals[0] += size
        totals[1] += t_wall
        totals[2] += t_cpu

    for (date, repo), totals in sorted(entries.items()):
        if min_size and totals[0] < min_size:
            continue

        print('%s\t%s\t%d\t%d\t%d' % (date, repo, totals[0], totals[1], totals[2]))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--min-size', type=int, default=0,
            help='Filter entries with transfer size less than this amount')

    options, args = parser.parse_args()

    aggregate(sys.stdin, min_size=options.min_size)
