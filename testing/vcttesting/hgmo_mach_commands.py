# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function, unicode_literals

import argparse
import os
import subprocess
import sys

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)


@CommandProvider
class HgmoCommands(object):
    def __init__(self, context):
        from vcttesting.docker import Docker, params_from_env
        from vcttesting.hgmo import HgCluster

        if 'HGMO_STATE_FILE' not in os.environ:
            print('Do not know where to store state.')
            print('Set the HGMO_STATE_FILE environment variable and try again.')
            sys.exit(1)

        if 'DOCKER_STATE_FILE' not in os.environ:
            print('Do not where to store Docker state.')
            print('Set the DOCKER_STATE_FILE environment variable and try again.')
            sys.exit(1)

        docker_url, tls = params_from_env(os.environ)
        docker = Docker(os.environ['DOCKER_STATE_FILE'], docker_url, tls=tls)
        if not docker.is_alive():
            print('Docker not available')
            sys.exit(1)
        self.c = HgCluster(docker, os.environ['HGMO_STATE_FILE'],
                           ldap_image=os.environ.get('DOCKER_LDAP_IMAGE'),
                           master_image=os.environ.get('DOCKER_HGMASTER_IMAGE'),
                           web_image=os.environ.get('DOCKER_HGWEB_IMAGE'))

    @Command('start', category='hgmo',
             description='Start a hg.mozilla.org cluster')
    @CommandArgument('--master-ssh-port', type=int,
                     help='Port number on which SSH server should listen')
    def start(self, master_ssh_port=None):
        s = self.c.start(master_ssh_port=master_ssh_port,
                         coverage='CODE_COVERAGE' in os.environ)
        print('SSH Hostname: %s' % s['master_ssh_hostname'])
        print('SSH Port: %s' % s['master_ssh_port'])
        print('LDAP URI: %s' % s['ldap_uri'])
        for url in s['web_urls']:
            print('Web URL: %s' % url)

    @Command('shellinit', category='hgmo',
             description='Print shell commands to export variables')
    def shellinit(self):
        print('export SSH_CID=%s' % self.c.master_id)
        print('export SSH_SERVER=%s' % self.c.master_ssh_hostname)
        print('export SSH_PORT=%d' % self.c.master_ssh_port)
        # Don't export the full value because spaces.
        print('export SSH_HOST_KEY=%s' % self.c.master_host_key.split()[1])
        for i, url in enumerate(self.c.web_urls):
            print('export HGWEB_%d_URL=%s' % (i, url))
        for i, cid in enumerate(self.c.web_ids):
            print('export HGWEB_%d_CID=%s' % (i, cid))
        for i, hostport in enumerate(self.c.kafka_hostports):
            print('export KAFKA_%d_HOSTPORT=%s' % (i, hostport))
        print('export ZOOKEEPER_CONNECT=%s' % self.c.zookeeper_connect)

    @Command('stop', category='hgmo',
             description='Stop a hg.mozilla.org cluster')
    def stop(self):
        self.c.stop()

    @Command('clean', category='hgmo',
             description='Clean up all references to this cluster')
    def clean(self):
        self.c.clean()

    @Command('create-ldap-user', category='hgmo',
             description='Create a new user in LDAP')
    @CommandArgument('email',
                     help='Email address associated with user')
    @CommandArgument('username',
                     help='System account name')
    @CommandArgument('uid', type=int,
                     help='Numeric user ID to associate with user')
    @CommandArgument('fullname',
                     help='Full name of the user')
    @CommandArgument('--key-file',
                     help='Use or create an SSH key')
    @CommandArgument('--scm-level', type=int, choices=(1, 2, 3),
                     help='Add the user to the specified SCM level groups')
    @CommandArgument('--no-hg-access', action='store_true',
                     help='Do not grant Mercurial access to user')
    def create_ldap_user(self, email, username, uid, fullname, key_file=None,
                         scm_level=None, no_hg_access=False):
        self.c.ldap.create_user(email, username, uid, fullname,
                                key_filename=key_file, scm_level=scm_level,
                                hg_access=not no_hg_access)

    @Command('add-ssh-key', category='hgmo',
             description='Add an SSH public key to a user')
    @CommandArgument('email',
                     help='Email address of user to modify')
    @CommandArgument('key',
                     help='SSH public key string')
    def add_ssh_key(self, email, key):
        if key == '-':
            key = sys.stdin.read().strip().encode('utf-8')
        self.c.ldap.add_ssh_key(email, key)

    @Command('create-repo', category='hgmo',
             description='Create a repository in the cluster')
    @CommandArgument('name',
                     help='Name of repository to create')
    @CommandArgument('level', type=int, choices=[1, 2, 3], default=1,
                     help='SCM level access for this repository')
    def create_repo(self, name, level):
        out = self.c.create_repo(name, level=level)
        if out:
            sys.stdout.write(out)

    @Command('aggregate-code-coverage', category='hgmo',
             description='Aggregate code coverage results to a directory')
    @CommandArgument('destdir',
                     help='Directory where to save code coverage files')
    def aggregate_code_coverage(self, destdir):
        self.c.aggregate_code_coverage(destdir)

    @Command('exec', category='hgmo',
             description='Execute a command in a Docker container')
    @CommandArgument('--detach', action='store_true',
                     help='Do not wait for process to finish')
    @CommandArgument('name', help='Name of container to execute inside')
    @CommandArgument('command', help='Command to execute',
                     nargs=argparse.REMAINDER)
    def execute(self, name, command, detach=False):
        if name == 'hgssh':
            cid = self.c.master_id
        elif name == 'pulse':
            cid = self.c.pulse_id
        elif name.startswith('hgweb'):
            i = int(name[5:])
            cid = self.c.web_ids[i]
        else:
            print('invalid name. must be "hgssh" or "hgwebN"')
            return 1

        args = '' if 'TESTTMP' in os.environ else '-it'
        if detach:
            args += ' -d '
        args = args.strip()

        return subprocess.call('docker exec %s %s %s' % (
                               args, cid, ' '.join(command)),
                               shell=True)
