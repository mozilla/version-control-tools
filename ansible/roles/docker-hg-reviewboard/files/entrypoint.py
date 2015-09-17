#!/usr/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

if 'LDAP_PORT_389_TCP_ADDR' not in os.environ:
    print('error: contained invoked without link to an ldap contaer')
    sys.exit(1)

ldap_url = 'ldap://%s:%s/' % (os.environ['LDAP_PORT_389_TCP_ADDR'],
                              os.environ['LDAP_PORT_389_TCP_PORT'])

os.environ['DOCKER_ENTRYPOINT'] = '1'

subprocess.check_call([
    '/usr/bin/python', '-u',
    '/usr/bin/ansible-playbook', 'docker-hgrb.yml',
        '-c', 'local',
        '-t', 'docker-startup',
        '-e', 'ldap_uri=%s' % ldap_url,
    ],
    cwd='/vct/ansible')

del os.environ['DOCKER_ENTRYPOINT']

subprocess.check_call(['/sbin/service', 'rsyslog', 'start'])

os.execl(sys.argv[1], *sys.argv[1:])
