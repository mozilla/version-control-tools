#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import grp
import os
import pwd
import stat
import sys

priv, pub = sys.argv[1:]

with open('/etc/mercurial/mirror', 'wb') as fh:
    fh.write(priv)

with open('/etc/mercurial/mirror.pub', 'wb') as fh:
    fh.write(pub)

os.chmod('/etc/mercurial/mirror', stat.S_IRUSR | stat.S_IWUSR)
os.chmod('/etc/mercurial/mirror.pub', stat.S_IRUSR | stat.S_IWUSR)

uhg = pwd.getpwnam('hg')
ghg = grp.getgrnam('hg')

os.chown('/etc/mercurial/mirror', uhg.pw_uid, ghg.gr_gid)
os.chown('/etc/mercurial/mirror.pub', uhg.pw_uid, ghg.gr_gid)

# Allow SSH connections from the master server.
with open('/home/hg/.ssh/authorized_keys', 'wb') as fh:
    fh.write('command="/usr/local/bin/mirror-pull -t /repo_local/mozilla/mozilla $SSH_ORIGINAL_COMMAND"')
    fh.write(',no-pty,no-x11-forwarding,no-agent-forwarding ')
    fh.write(pub.strip())
    fh.write('\n')

os.chown('/home/hg/.ssh/authorized_keys', uhg.pw_uid, ghg.gr_gid)
os.chmod('/home/hg/.ssh/authorized_keys', stat.S_IRUSR | stat.S_IWUSR)
