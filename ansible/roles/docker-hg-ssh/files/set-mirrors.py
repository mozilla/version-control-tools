#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

with open('/etc/mercurial/mirrors', 'wb') as fh:
    for mirror in sys.argv[1:]:
        fh.write(mirror)
        fh.write('\n')
