#!/usr/bin/env python2.7
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Adjust mtime of 00changelog.i to last pushlog time.

This makes the "last modified date" of the repo in the web interface
somewhat accurate.
"""

import datetime
import os
import sqlite3
import sys


for path in sys.stdin:
    path = path.strip()

    pushlog = os.path.join(path, '.hg', 'pushlog2.db')
    if not os.path.exists(pushlog):
        print('no pushlog: %s' % pushlog)
        continue

    cl_path = os.path.join(path, '.hg', 'store', '00changelog.i')
    if not os.path.exists(cl_path):
        print('no changelog: %s' % cl_path)
        continue

    conn = sqlite3.connect(pushlog)
    try:
        res = conn.execute('SELECT MAX(date) FROM pushlog').fetchone()
        if not res or not res[0]:
            print('no pushlog entry for %s' % path)
            continue

        last_push_time = res[0]
    finally:
        conn.close()

    current_mtime = os.path.getmtime(cl_path)

    if current_mtime == last_push_time:
        continue

    current_atime = os.path.getatime(cl_path)

    current_dt = datetime.datetime.utcfromtimestamp(current_mtime)
    push_dt = datetime.datetime.utcfromtimestamp(last_push_time)
    print('Changing mtime of %s from %s to %s' % (
          path, current_dt.isoformat(), push_dt.isoformat()))

    os.utime(cl_path, (current_atime, last_push_time))
