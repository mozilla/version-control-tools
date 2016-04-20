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

if 'PULSE_PORT_5672_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to a pulse container')
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

pulse_hostname = os.environ['PULSE_PORT_5672_TCP_ADDR']
pulse_port = int(os.environ['PULSE_PORT_5672_TCP_PORT'])

# Generate host SSH keys for hg.
if not os.path.exists('/etc/mercurial/ssh/ssh_host_ed25519_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'ed25519',
                           '-f', '/etc/mercurial/ssh/ssh_host_ed25519_key', '-N', ''])

if not os.path.exists('/etc/mercurial/ssh/ssh_host_rsa_key'):
    subprocess.check_call(['/usr/bin/ssh-keygen', '-t', 'rsa', '-b', '4096',
                           '-f', '/etc/mercurial/ssh/ssh_host_rsa_key', '-N', ''])

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

kafka_state = open('/kafka-servers', 'rb').read().splitlines()

# Update the Kafka connect servers in the vcsreplicator config.
monitor_groups = kafka_state[2].split(',')
kafka_servers = kafka_state[3:]
kafka_servers = ['%s:9092' % s.split(':')[0] for s in kafka_servers]

hgrc_lines = open('/etc/mercurial/hgrc', 'rb').readlines()
with open('/etc/mercurial/hgrc', 'wb') as fh:
    for line in hgrc_lines:
        # This isn't the most robust ini parsing logic in the world, but it
        # gets the job done.
        if line.startswith('hosts = '):
            line = 'hosts = %s\n' % ', '.join(kafka_servers)

        fh.write(line)

pushdataaggregator_lines = open('/etc/mercurial/pushdataaggregator.ini', 'rb').readlines()
with open('/etc/mercurial/pushdataaggregator.ini', 'wb') as fh:
    for line in pushdataaggregator_lines:
        if line.startswith('hosts ='):
            line = 'hosts = %s\n' % ', '.join(kafka_servers)

        fh.write(line)

with open('/etc/mercurial/pushdataaggregator_groups', 'wb') as fh:
    fh.write('\n'.join(monitor_groups))

# Update the notification daemon settings.
notification_lines = open('/etc/mercurial/notifications.ini', 'rb').readlines()
with open('/etc/mercurial/notifications.ini', 'wb') as fh:
    section = None
    for line in notification_lines:
        if line.startswith('['):
            section = line.strip()[1:-1]

        if section == 'pulseconsumer':
            if line.startswith('hosts ='):
                line = 'hosts = %s\n' % ', '.join(kafka_servers)

        if section == 'pulse':
            if line.startswith('hostname ='):
                line = 'hostname = %s\n' % pulse_hostname
            elif line.startswith('port ='):
                line = 'port = %d\n' % pulse_port
            # SSL isn't enabled in Docker.
            elif line.startswith('ssl ='):
                line = 'ssl = false\n'

        fh.write(line)

os.execl(sys.argv[1], *sys.argv[1:])
