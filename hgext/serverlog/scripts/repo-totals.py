#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

def repo_totals(fh):
    repos = {}

    for line in fh:
        parts = line.rstrip().split()

        date, repo, ip, command, size, t_wall, t_cpu = parts
        size = int(size)
        t_wall = float(t_wall)
        t_cpu = float(t_cpu)

        totals = repos.setdefault(repo, [0, 0.0, 0.0])
        totals[0] += size
        totals[1] += t_wall
        totals[2] += t_cpu

    for repo, totals in sorted(repos.items()):
        print('%s\t%d\t%d\t%d' % (repo, totals[0], totals[1], totals[2]))

if __name__ == '__main__':
    repo_totals(sys.stdin)
