# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function, unicode_literals

import os
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
        if not docker_url:
            print('Docker not available')
            sys.exit(1)

        docker = Docker(os.environ['DOCKER_STATE_FILE'], docker_url, tls=tls)
        self.c = HgCluster(docker, os.environ['HGMO_STATE_FILE'],
                           ldap_image=os.environ.get('DOCKER_LDAP_IMAGE'),
                           master_image=os.environ.get('DOCKER_HGMASTER_IMAGE'),
                           web_image=os.environ.get('DOCKER_HGWEB_IMAGE'))

    @Command('start', category='hgmo',
             description='Start a hg.mozilla.org cluster')
    @CommandArgument('--master-ssh-port', type=int,
                     help='Port number on which SSH server should listen')
    def start(self, master_ssh_port=None):
        s = self.c.start(master_ssh_port=master_ssh_port)
        print('SSH Hostname: %s' % s['master_ssh_hostname'])
        print('SSH Port: %s' % s['master_ssh_port'])
        print('LDAP URI: %s' % s['ldap_uri'])
        for url in s['web_urls']:
            print('Web URL: %s' % url)

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
    def create_ldap_user(self, email, username, uid, fullname, key_file=None):
        self.c.create_ldap_user(email, username, uid, fullname,
                                key_filename=key_file)

    @Command('add-ssh-key', category='hgmo',
             description='Add an SSH public key to a user')
    @CommandArgument('email',
                     help='Email address of user to modify')
    @CommandArgument('key',
                     help='SSH public key string')
    def add_ssh_key(self, email, key):
        if key == '-':
            key = sys.stdin.read().strip().encode('utf-8')
        self.c.add_ssh_key(email, key)

    @Command('create-repo', category='hgmo',
             description='Create a repository in the cluster')
    @CommandArgument('name',
                     help='Name of repository to create')
    @CommandArgument('level', type=int, choices=[1, 2, 3], default=1,
                     help='SCM level access for this repository')
    def create_repo(self, name, level):
        self.c.create_repo(name, level=level)
