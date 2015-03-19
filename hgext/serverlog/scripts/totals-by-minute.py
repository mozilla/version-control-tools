#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import sys

def totals_by_minute(fh):
    minutes = {}

    for line in fh:
        parts = line.rstrip().split()

        when, repo, ip, command, size, t_wall, t_cpu = parts
        when = datetime.datetime.strptime(when, '%Y-%m-%dT%H:%M:%S')
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        t = when.time().replace(second=0, microsecond=0)
        when = when.combine(when.date(), t)

        totals = minutes.setdefault(when, [0, 0.0, 0.0])
        totals[0] += size
        totals[1] += t_wall
        totals[2] += t_cpu

    for date, totals in sorted(minutes.items()):
        print('%s\t%d\t%d\t%d' % (date.isoformat(), totals[0], totals[1], totals[2]))

if __name__ == '__main__':
    totals_by_minute(sys.stdin)
