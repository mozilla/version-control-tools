#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

def aggregate(fh):
    days = {}

    for line in fh:
        parts = line.rstrip().split()

        when, count, size, t_wall, t_cpu = parts
        count = int(count)
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        totals = days.setdefault(when, [0, 0, 0.0, 0.0])
        totals[0] += count
        totals[1] += size
        totals[2] += t_wall
        totals[3] += t_cpu

    for date, totals in sorted(days.items()):
        print('%s\t%d\t%d\t%d\t%d' % (date, totals[0], totals[1], totals[2],
                                      totals[3]))

if __name__ == '__main__':
    aggregate(sys.stdin)
