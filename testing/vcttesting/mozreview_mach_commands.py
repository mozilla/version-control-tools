# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os
import subprocess

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

@CommandProvider
class MozReviewCommands(object):
    def _get_mozreview(self, where):
        if not where and 'MOZREVIEW_HOME' in os.environ:
            where = os.environ['MOZREVIEW_HOME']

        db_image = os.environ.get('DOCKER_BMO_DB_IMAGE')
        web_image = os.environ.get('DOCKER_BMO_WEB_IMAGE')
        hgrb_image = os.environ.get('DOCKER_HGRB_IMAGE')
        ldap_image = os.environ.get('DOCKER_LDAP_IMAGE')
        pulse_image = os.environ.get('DOCKER_PULSE_IMAGE')
        rbweb_image = os.environ.get('DOCKER_RBWEB_IMAGE')
        autolanddb_image = os.environ.get('DOCKER_AUTOLANDDB_IMAGE')
        autoland_image = os.environ.get('DOCKER_AUTOLAND_IMAGE')

        from vcttesting.mozreview import MozReview
        return MozReview(where, db_image=db_image, web_image=web_image,
                         hgrb_image=hgrb_image, ldap_image=ldap_image,
                         pulse_image=pulse_image, rbweb_image=rbweb_image,
                         autolanddb_image=autolanddb_image,
                         autoland_image=autoland_image)

    @Command('start', category='mozreview',
        description='Start a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('--bugzilla-port', type=int,
        help='Port Bugzilla HTTP server should listen on.')
    @CommandArgument('--reviewboard-port', type=int,
        help='Port Review Board HTTP server should listen on.')
    @CommandArgument('--mercurial-port', type=int,
        help='Port Mercurial HTTP server should listen on.')
    @CommandArgument('--pulse-port', type=int,
        help='Port Pulse should listen on.')
    @CommandArgument('--autoland-port', type=int,
        help='Port Autoland should listen on.')
    @CommandArgument('--ldap-port', type=int,
                     help='Port LDAP server should listen on.')
    @CommandArgument('--ssh-port', type=int,
                     help='Port Mercurial SSH server should listen on.')
    def start(self, where, bugzilla_port=None, reviewboard_port=None,
            mercurial_port=None, pulse_port=None, autoland_port=None,
            ldap_port=None, ssh_port=None):
        mr = self._get_mozreview(where)
        mr.start(bugzilla_port=bugzilla_port,
                reviewboard_port=reviewboard_port,
                mercurial_port=mercurial_port,
                pulse_port=pulse_port,
                autoland_port=autoland_port,
                ldap_port=ldap_port,
                ssh_port=ssh_port,
                verbose=True)

        print('Bugzilla URL: %s' % mr.bugzilla_url)
        print('Review Board URL: %s' % mr.reviewboard_url)
        print('Mercurial URL: %s' % mr.mercurial_url)
        print('Pulse endpoint: %s:%s' % (mr.pulse_host, mr.pulse_port))
        print('Autoland URL: %s' % mr.autoland_url)
        print('Admin username: %s' % mr.admin_username)
        print('Admin password: %s' % mr.admin_password)
        print('LDAP URI: %s' % mr.ldap_uri)
        print('HG Push URL: ssh://%s:%d/' % (mr.ssh_hostname, mr.ssh_port))
        print('')
        print('Run the following to use this instance with all future commands:')
        print('  export MOZREVIEW_HOME=%s' % mr._path)
        print('')
        print('Refresh code in the cluster by running:')
        print('  ./mozreview refresh')
        print('')
        print('Perform refreshing automatically by running:')
        print('  ./mozreview autorefresh')
        print('')
        print('(autorefresh requires `watchman`)')
        print('')
        print('Obtain a shell in a container by running:')
        print('  ./mozreview shell <container>')
        print('')
        print('(valid container names include: rbweb, bmoweb, hgrb, autoland)')

    @Command('shellinit', category='mozreview',
             description='Print statements to export variables to shells.')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    def shellinit(self, where):
        mr = self._get_mozreview(where)

        print('export MOZREVIEW_HOME=%s' % mr._path)
        print('export BUGZILLA_URL=%s' % mr.bugzilla_url)
        print('export REVIEWBOARD_URL=%s' % mr.reviewboard_url)
        print('export MERCURIAL_URL=%s' % mr.mercurial_url)
        print('export AUTOLAND_URL=%s' % mr.autoland_url)
        print('export ADMIN_USERNAME=%s' % mr.admin_username)
        print('export ADMIN_PASSWORD=%s' % mr.admin_password)
        print('export HGSSH_HOST=%s' % mr.ssh_hostname)
        print('export HGSSH_PORT=%d' % mr.ssh_port)
        print('export PULSE_HOST=%s' % mr.pulse_host)
        print('export PULSE_PORT=%d' % mr.pulse_port)

    @Command('stop', category='mozreview',
        description='Stop a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    def stop(self, where):
        mr = self._get_mozreview(where)
        mr.stop()

    @Command('refresh', category='mozreview',
             description='Refresh a running MozReview cluster with latest code')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    def refresh(self, where):
        mr = self._get_mozreview(where)
        mr.refresh(verbose=True)

    @Command('autorefresh', category='mozreview',
             description='Automatically refresh containers when files change')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    def autorefresh(self, where):
        mr = self._get_mozreview(where)
        mr.start_autorefresh()

    @Command('create-repo', category='mozreview',
        description='Add a repository to a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('path', help='Relative path of repository')
    def create_repo(self, where, path):
        mr = self._get_mozreview(where)
        http_url, ssh_url, rbid = mr.create_repository(path)
        print('HTTP URL (read only): %s' % http_url)
        print('SSH URL (read+write): %s' % ssh_url)

    @Command('create-user', category='mozreview',
        description='Create a user in a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('email', help='Email address for user')
    @CommandArgument('password', help='Password for user')
    @CommandArgument('fullname', help='Full name for user')
    @CommandArgument('--uid', type=int,
                     help='Numeric user ID for user')
    @CommandArgument('--scm-level', type=int, choices=(1, 2, 3),
                     help='Source code access level to grant to user')
    def create_user(self, where, email, password, fullname, uid=None,
                    scm_level=None):
        mr = self._get_mozreview(where)
        u = mr.create_user(email, password, fullname, uid=uid, scm_level=None)
        print('Created user %s' % u['bugzilla']['id'])

    @Command('create-ldap-user', category='mozreview',
             description='Create a user in the LDAP server')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    @CommandArgument('email',
                     help='Email address associated with user')
    @CommandArgument('username',
                     help='System account name')
    @CommandArgument('uid', type=int,
                     help='Numeric user ID to associate with user')
    @CommandArgument('fullname',
                     help='Full name of user')
    @CommandArgument('--key-file',
                     help='Path to SSH key to use or create (if missing)')
    @CommandArgument('--scm-level', type=int, choices=(1, 2, 3),
                     help='Source code level access to grant to the user')
    def create_ldap_user(self, where, email, username, uid, fullname,
                         key_file=None, scm_level=None):
        mr = self._get_mozreview(where)
        mr.get_ldap().create_user(email, username, uid, fullname,
                                  key_filename=key_file, scm_level=scm_level)

    @Command('exec', category='mozreview',
             description='Execute a command in a Docker container')
    @CommandArgument('name', help='Name of container to shell into',
                     choices={'bmoweb', 'bmodb', 'pulse', 'rbweb', 'hgrb',
                              'autoland'})
    @CommandArgument('command', help='Command to execute',
                     nargs=argparse.REMAINDER)
    def execute(self, name, command):
        mr = self._get_mozreview(None)

        cid = getattr(mr, '%s_id' % name, None)
        if not cid:
            print('No container for %s was found running' % name)
            return 1

        args = '' if 'TESTTMP' in os.environ else '-it'

        return subprocess.call('docker exec %s %s %s' %
                              (args, cid, ' '.join(command)),
                              shell=True)

    @Command('shell', category='mozreview',
             description='Start a shell inside a running container')
    @CommandArgument('name', help='Name of container to shell into',
                     choices={'bmoweb', 'bmodb', 'pulse', 'rbweb', 'hgrb',
                              'autoland'})
    def shell(self, name):
        return self.execute(name, ['/bin/bash'])
