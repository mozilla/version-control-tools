#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from optparse import OptionParser
import sys

def aggregate(fh, min_size=0, min_requests=0):
    entries = {}

    for line in fh:
        parts = line.rstrip().split()

        when, repo, count, size, t_wall, t_cpu = parts
        count = int(count)
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        totals = entries.setdefault((when, repo), [0, 0, 0.0, 0.0])
        totals[0] += count
        totals[1] += size
        totals[2] += t_wall
        totals[3] += t_cpu

    for (date, repo), totals in sorted(entries.items()):
        if min_requests and totals[0] < min_requests:
            continue
        if min_size and totals[1] < min_size:
            continue

        print('%s\t%s\t%d\t%d\t%d\t%d' % (date, repo, totals[0], totals[1],
                                          totals[2], totals[3]))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--min-size', type=int, default=0,
            help='Filter entries with transfer size less than this amount')
    parser.add_option('--min-requests', type=int, default=0,
            help='Filter entries with at least this many requests per interval')

    options, args = parser.parse_args()

    aggregate(sys.stdin, min_size=options.min_size,
              min_requests=options.min_requests)
