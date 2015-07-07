#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Reads parsed logs from stdin and writes to per-daily output files
# in the directory specified.

import os
import sys


def write_daily_logs(fh, path):
    ofs = {}
    for line in fh:
        date = line[0:10]
        of = ofs.get(date, None)
        if not of:
            of = open(os.path.join(path, 'parsed-%s' % date), 'wb')
            ofs[date] = of

        of.write(line)

    for of in ofs.values():
        of.close()


if __name__ == '__main__':
    write_daily_logs(sys.stdin, sys.argv[1])
