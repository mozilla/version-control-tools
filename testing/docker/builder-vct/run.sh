#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -e

cat > /etc/rsyncd.conf << EOF
uid = root
gid = root
use chroot = yes
pid file = /var/run/rsyncd.pid
log file = /dev/stdout

[vct-mount]
  hosts allow = *
  read only = false
  path = /vct-mount
EOF

exec /usr/bin/rsync --no-detach --daemon --config /etc/rsyncd.conf "$@"
