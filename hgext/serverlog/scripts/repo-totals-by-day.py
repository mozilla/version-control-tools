#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import sys

def totals_by_day(fh, by_command=False):
    days = {}

    for line in fh:
        parts = line.rstrip().split()

        try:
            when, repo, ip, command, size, t_wall, t_cpu = parts
            when = datetime.datetime.strptime(when, '%Y-%m-%dT%H:%M:%S')
        except (TypeError, ValueError):
            continue

        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        date = when.date()

        repos = days.setdefault(date, {})
        totals = repos.setdefault((repo, command), [0, 0, 0.0, 0.0])
        all_totals = repos.setdefault((repo, 'all'), [0, 0, 0.0, 0.0])
        totals[0] += 1
        all_totals[0] += 1
        totals[1] += size
        all_totals[1] += size
        totals[2] += t_wall
        all_totals[2] += t_wall
        totals[3] += t_cpu
        all_totals[3] += t_cpu

    for date, repos in sorted(days.items()):
        for (repo, command), totals in sorted(repos.items()):
            if by_command:
                print('%s\t%s\t%s\t%d\t%d\t%d\t%d' % (
                    date.isoformat(),
                    repo,
                    command,
                    totals[0],
                    totals[1],
                    totals[2],
                    totals[3],
                ))
            else:
                if command != 'all':
                    continue

                print('%s\t%s\t%d\t%d\t%d\t%d' % (
                    date.isoformat(),
                    repo,
                    totals[0],
                    totals[1],
                    totals[2],
                    totals[3],
                ))

if __name__ == '__main__':
    totals_by_day(sys.stdin, by_command='--by-command' in sys.argv)
