#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Add some guards around a mysql dump file to make importing faster.
# See https://dev.mysql.com/doc/refman/5.6/en/optimizing-innodb-bulk-data-loading.html

from __future__ import print_function

import sys

# These drastically cut down on I/O during bulk import and make importing
# significantly faster, even on solid state storage.
print('SET unique_checks=0;')
print('SET foreign_key_checks=0;')

while True:
    data = sys.stdin.read(32768)
    if not data:
        break

    sys.stdout.write(data)
