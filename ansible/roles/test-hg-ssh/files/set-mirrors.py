#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

with open('/etc/mercurial/mirrors', 'w') as mirrors:
    with open('/etc/mercurial/known_hosts', 'w') as kh:
        ips = sys.argv[1::2]
        keys = sys.argv[2::2]
        for ip, key in zip(ips, keys):
            mirrors.write(ip)
            mirrors.write('\n')

            kh.write('%s %s\n' % (ip, key))
