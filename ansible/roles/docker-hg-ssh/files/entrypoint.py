#!/usr/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

if 'LDAP_PORT_389_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to an ldap container')
    sys.exit(1)

os.environ['DOCKER_ENTRYPOINT'] = '1'

subprocess.check_call([
    '/usr/bin/python', '-u',
    '/usr/bin/ansible-playbook', 'docker-hgmaster.yml', '-c', 'local',
    '-t', 'docker-startup'],
    cwd='/vct/ansible')

del os.environ['DOCKER_ENTRYPOINT']

ldap_hostname = os.environ['LDAP_PORT_389_TCP_ADDR']
ldap_port = os.environ['LDAP_PORT_389_TCP_PORT']
ldap_uri = 'ldap://%s:%s/' % (ldap_hostname, ldap_port)

# Generate host SSH keys.
if not os.path.exists('/etc/ssh/ssh_host_dsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'dsa',
                           '-f', '/etc/ssh/ssh_host_dsa_key'])

if not os.path.exists('/etc/ssh/ssh_host_rsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'rsa', '-b', '2048',
                           '-f', '/etc/ssh/ssh_host_rsa_key'])

ldap_conf = open('/etc/mercurial/ldap.json', 'rb').readlines()
with open('/etc/mercurial/ldap.json', 'wb') as fh:
    for line in ldap_conf:
        line = line.replace('%url%', ldap_uri)
        line = line.replace('%writeurl%', ldap_uri)
        fh.write(line)

# Set up code coverage, if requested.
if 'CODE_COVERAGE' in os.environ:
    with open('/collect-coverage', 'a'):
        pass
else:
    try:
        os.unlink('/collect-coverage')
    except OSError:
        pass

subprocess.check_call(['/entrypoint-kafkabroker'])

# Update the Kafka connect servers in the vcsreplicator config.
kafka_servers = open('/kafka-servers', 'rb').read().splitlines()[2:]
kafka_servers = ['%s:9092' % s.split(':')[0] for s in kafka_servers]
hgrc_lines = open('/etc/mercurial/hgrc-vcsreplicator', 'rb').readlines()
with open('/etc/mercurial/hgrc-vcsreplicator', 'wb') as fh:
    for line in hgrc_lines:
        if line.startswith('hosts = '):
            line = 'hosts = %s\n' % ', '.join(kafka_servers)

        fh.write(line)

subprocess.check_call(['/sbin/service', 'rsyslog', 'start'])

os.execl(sys.argv[1], *sys.argv[1:])
