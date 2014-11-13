#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import sys

def totals_by_day(fh):
    days = {}

    for line in fh:
        parts = line.rstrip().split()

        try:
            when, repo, ip, command, size, t_wall, t_cpu = parts
        except ValueError:
            continue

        when = datetime.datetime.strptime(when, '%Y-%m-%dT%H:%M:%S')
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        date = when.date()

        repos = days.setdefault(date, {})
        totals = repos.setdefault(repo, [0, 0.0, 0.0])
        totals[0] += size
        totals[1] += t_wall
        totals[2] += t_cpu

    for date, repos in sorted(days.items()):
        for repo in totals in sorted(repos.items()):
            print('%s\t%s\t%d\t%d\t%d' % (
                date.isoformat(), repo, totals[0], totals[1], totals[2]))

if __name__ == '__main__':
    totals_by_day(sys.stdin)

