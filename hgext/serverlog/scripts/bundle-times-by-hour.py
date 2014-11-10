#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import sys

def bundle_times_by_hour(fh):
    repos = {}

    for line in fh:
        parts = line.rstrip().split()

        date, repo, ip, command, size, t_wall, t_cpu = parts
        date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        if command != 'getbundle':
            continue

        date = datetime.datetime(year=date.year, month=date.month,
                day=date.day, hour=date.hour)

        hours = repos.setdefault(repo, {})
        hours.setdefault(date, []).append((t_wall, t_cpu))

    for repo, hours in sorted(repos.items()):
        for hour, times in sorted(hours.items()):
            wall = float(sum([t[0] for t in times])) / len(times)
            cpu = float(sum([t[1] for t in times])) / len(times)
            print('%s %s %.2f %.2f' % (repo, hour.isoformat(), wall, cpu))

if __name__ == '__main__':
    bundle_times_by_hour(sys.stdin)
