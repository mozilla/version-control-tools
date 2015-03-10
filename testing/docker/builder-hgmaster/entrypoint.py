#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

# Disable output buffering.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = sys.stdout

if 'LDAP_PORT_389_TCP_ADDR' not in os.environ:
    print('error: container invoked improperly. please link to an ldap container')
    sys.exit(1)

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

# System wide LDAP configuration
with open('/etc/openldap/ldap.conf', 'wb') as fh:
    fh.write('\n'.join([
        'BASE dc=mozilla',
        'URI %s' % ldap_uri,
    ]))

# Configure PAM LDAP
with open('/etc/pam_ldap.conf', 'wb') as fh:
    fh.write('\n'.join([
        'base dc=mozilla',
        'binddn cn=admin,dc=mozilla',
        'bindpw password',
        'uri %s' % ldap_uri,
        'ssl off',
        'pam_password md5',
    ]))

# Update the LDAP server in OpenSSH config.
sshd_config = open('/etc/ssh/sshd_config', 'rb').readlines()
with open('/etc/ssh/sshd_config', 'wb') as fh:
    for line in sshd_config:
        if line.startswith('LpkServers'):
            line = 'LpkServers %s\n' % ldap_uri

        fh.write(line)

nslcd_config = open('/etc/nslcd.conf', 'rb').readlines()
with open('/etc/nslcd.conf', 'wb') as fh:
    for line in nslcd_config:
        if line.startswith('uri '):
            line = 'uri %s\n' % ldap_uri

        fh.write(line)

REPLACEMENTS = {
    "<%= scope.function_hiera(['secrets_openldap_moco_bindhg_username']) %>": 'cn=admin,dc=mozilla',
    "<%= scope.function_hiera(['secrets_openldap_moco_bindhg_password']) %>": 'password',
    "<%= scope.lookupvar('::ldapvip') %>": '%s:%s/' % (ldap_hostname, ldap_port),
}

ldap_helper = open('/usr/local/bin/ldap_helper.py', 'rb').readlines()
with open('/usr/local/bin/ldap_helper.py', 'wb') as fh:
    for line in ldap_helper:
        for s, r in REPLACEMENTS.items():
            line = line.replace(s, r)

        fh.write(line)

hg_helper = open('/usr/local/bin/hg_helper.py', 'rb').readlines()
with open('/usr/local/bin/hg_helper.py', 'wb') as fh:
    for line in hg_helper:
        line = line.replace('ldap://ldap.db.scl3.mozilla.com', ldap_uri)
        fh.write(line)

pash = open('/usr/local/bin/pash.py', 'rb').readlines()
with open('/usr/local/bin/pash.py', 'wb') as fh:
    for line in pash:
        line = line.replace('ldap://ldap.db.scl3.mozilla.com', ldap_uri)
        line = line.replace('ldap://ldapsync1.db.scl3.mozilla.com', ldap_uri)
        fh.write(line)

subprocess.check_call([
    '/usr/sbin/authconfig',
    '--enablemkhomedir',
    '--enableldap',
    '--enableldapauth',
    '--ldapserver=%s' % ldap_uri,
    '--ldapbasedn=dc=mozilla',
    '--updateall'])

subprocess.check_call(['/sbin/service', 'rsyslog', 'start'])

os.execl(sys.argv[1], *sys.argv[1:])
