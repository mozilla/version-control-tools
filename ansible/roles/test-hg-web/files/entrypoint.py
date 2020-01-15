#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import socket
import subprocess
import sys

# Disable output buffering.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = sys.stdout

ssh_hostname = 'hgssh'
hostname = socket.gethostname()

if not os.path.exists('/etc/ssh/ssh_host_ed25519_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'ed25519',
                           '-f', '/etc/ssh/ssh_host_ed25519_key', '-N', ''])

if not os.path.exists('/etc/ssh/ssh_host_rsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'rsa', '-b', '2048',
                           '-f', '/etc/ssh/ssh_host_rsa_key', '-N', ''])

REPLACEMENTS = {
    '@mirror_source@': ssh_hostname,
}

mirror_pull = open('/usr/local/bin/mirror-pull', 'rb').readlines()
with open('/usr/local/bin/mirror-pull', 'wb') as fh:
    for line in mirror_pull:
        for k, v in REPLACEMENTS.items():
            line = line.replace(k, v)

        fh.write(line)

REWRITE_CONSUMER_CONFIGS = (
    '/etc/mercurial/vcsreplicator.ini',
    '/etc/mercurial/vcsreplicator-pending.ini',
)

for f in REWRITE_CONSUMER_CONFIGS:
    vcsreplicator = open(f, 'rb').readlines()
    with open(f, 'wb') as fh:
        for line in vcsreplicator:
            for k, v in REPLACEMENTS.items():
                line = line.replace(k, v)

            # The client config file defines the client ID and group, which are
            # used for offset management. Since the file contents come from
            # the same container, we need to update the per-container values
            # at container start time to something unique. We choose the
            # hostname of the container, which should be unique.
            if line.startswith('client_id ='):
                line = 'client_id = %s\n' % hostname
            elif line.startswith('group = '):
                line = 'group = %s\n' % hostname

            fh.write(line)

# Replace SSH config for master server with the current environment's.
ssh_config = open('/home/hg/.ssh/config', 'rb').readlines()
with open('/home/hg/.ssh/config', 'wb') as fh:
    for line in ssh_config:
        if line.startswith('Host hg.mozilla.org'):
            line = 'Host %s\n' % ssh_hostname
        elif line.startswith('    Hostname'):
            line = '    #%s' % line

        fh.write(line)

# Grab SSH host key from master. We'll get a prompt to accept the host key on
# first connection unless we do this (since strict host key checking is on).
p = subprocess.Popen(['/usr/bin/ssh-keyscan', '-H', ssh_hostname],
                     stdout=subprocess.PIPE)
out = p.communicate()[0]
if p.wait():
    raise Exception('ssh-keyscan errored')

with open('/home/hg/.ssh/known_hosts', 'wb') as fh:
    fh.write(out)

subprocess.check_call(['/entrypoint-kafkabroker'])

os.execl(sys.argv[1], *sys.argv[1:])
