#!/usr/bin/python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

# Disable output buffering.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = sys.stdout

if 'MASTER_PORT_22_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to a master container')
    sys.exit(1)

if not os.path.exists('/etc/ssh/ssh_host_dsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'dsa',
                           '-f', '/etc/ssh/ssh_host_dsa_key'])

if not os.path.exists('/etc/ssh/ssh_host_rsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'rsa', '-b', '2048',
                           '-f', '/etc/ssh/ssh_host_rsa_key'])

REPLACEMENTS = {
    '<%= @mirror_source %>': os.environ['MASTER_PORT_22_TCP_ADDR'],
    '<%= @repo_serve_path %>': '/repo_local/mozilla/mozilla',
    '%<= @repo_serve_path %>': '/repo_local/mozilla/mozilla',
    '<%= @python_lib_override_path %>': '/repo_local/mozilla/library_overrides',
    '<%= @python_lib_path %>': '/repo_local/mozilla/libraries',
    '<%= @mirror_priv_key_path %>': '/etc/mercurial/mirror',
    '<%= @mirror_user_name %>': 'hg',
}

mirror_pull = open('/usr/local/bin/mirror-pull', 'rb').readlines()
with open('/usr/local/bin/mirror-pull', 'wb') as fh:
    for line in mirror_pull:
        for k, v in REPLACEMENTS.items():
            line = line.replace(k, v)

        fh.write(line)

os.execl(sys.argv[1], *sys.argv[1:])
