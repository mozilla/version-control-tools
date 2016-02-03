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

        web_image = os.environ.get('DOCKER_BMO_WEB_IMAGE')
        hgrb_image = os.environ.get('DOCKER_HGRB_IMAGE')
        ldap_image = os.environ.get('DOCKER_LDAP_IMAGE')
        pulse_image = os.environ.get('DOCKER_PULSE_IMAGE')
        rbweb_image = os.environ.get('DOCKER_RBWEB_IMAGE')
        autolanddb_image = os.environ.get('DOCKER_AUTOLANDDB_IMAGE')
        autoland_image = os.environ.get('DOCKER_AUTOLAND_IMAGE')
        hgweb_image = os.environ.get('DOCKER_HGWEB_IMAGE')
        treestatus_image = os.environ.get('DOCKER_TREESTATUS_IMAGE')

        from vcttesting.mozreview import MozReview
        return MozReview(where, web_image=web_image,
                         hgrb_image=hgrb_image, ldap_image=ldap_image,
                         pulse_image=pulse_image, rbweb_image=rbweb_image,
                         autolanddb_image=autolanddb_image,
                         autoland_image=autoland_image,
                         hgweb_image=hgweb_image,
                         treestatus_image=treestatus_image)

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
    @CommandArgument('--hgweb-port', type=int,
                     help='Port hg.mo HTTP server should listen on.')
    @CommandArgument('--treestatus-port', type=int,
                     help='Port treestatus HTTP server should listen on.')
    def start(self, where, bugzilla_port=None, reviewboard_port=None,
            mercurial_port=None, pulse_port=None, autoland_port=None,
            ldap_port=None, ssh_port=None, hgweb_port=None,
            treestatus_port=None):
        mr = self._get_mozreview(where)
        mr.start(bugzilla_port=bugzilla_port,
                reviewboard_port=reviewboard_port,
                mercurial_port=mercurial_port,
                pulse_port=pulse_port,
                autoland_port=autoland_port,
                ldap_port=ldap_port,
                ssh_port=ssh_port,
                hgweb_port=hgweb_port,
                treestatus_port=treestatus_port,
                verbose=True)

        print('Bugzilla URL: %s' % mr.bugzilla_url)
        print('Review Board URL: %s' % mr.reviewboard_url)
        print('Mercurial RB URL: %s' % mr.mercurial_url)
        print('hg.mo URL: %s' % mr.hgweb_url)
        print('Pulse endpoint: %s:%s' % (mr.pulse_host, mr.pulse_port))
        print('Autoland URL: %s' % mr.autoland_url)
        print('Treestatus URL: %s' % mr.treestatus_url)
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
        print('export HGWEB_URL=%s' % mr.hgweb_url)
        print('export AUTOLAND_URL=%s' % mr.autoland_url)
        print('export TREESTATUS_URL=%s' % mr.treestatus_url)
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
        print('')
        print('Run the following to create a configured clone:')
        print('  ./mozreview clone %s /path/to/clone' % path)
        print('')
        print('And a clone bound to a particular user:')
        print('  ./mozreview clone %s /path/to/clone --user <user>' % path)

    @Command('clone', category='mozreview',
             description='Clone and configure a MozReview repository')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    @CommandArgument('repo',
                     help='Name of repository to clone')
    @CommandArgument('dest',
                     help='Where to clone repository to')
    @CommandArgument('--user',
                     help='User to attach to the repository')
    def clone(self, where, repo, dest, user=None):
        """Clone a review repository such that it easily integrates with MozReview.

        The specified review repository is cloned. In addition, appropriate
        Mercurial configurations are installed to make pushing to the review
        repository simple.

        If a username is specified via ``--user``, the repository is "bound"
        to that user: credentials are defined and all operations against the
        repository are performed as that user.
        """
        mr = self._get_mozreview(where)
        mr.clone(repo, dest, username=user)

    @Command('create-user', category='mozreview',
             description='Create a user in a MozReview instance')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    @CommandArgument('email', help='Email address for user')
    @CommandArgument('password', help='Password for user')
    @CommandArgument('fullname', help='Full name for user')
    @CommandArgument('--uid', type=int,
                     help='Numeric user ID for user')
    @CommandArgument('--username',
                     help='System account name; defaults to username part of '
                     'email address')
    @CommandArgument('--key-file',
                     help='Path to SSH key to use or create (if missing)')
    @CommandArgument('--scm-level', type=int, choices=(1, 2, 3),
                     help='Source code access level to grant to user')
    @CommandArgument('--bugzilla-group', action='append',
                     help='Bugzilla group to add user to.')
    @CommandArgument('--no-api-key', action='store_true',
                     help='Do not create an API key for this user.')
    @CommandArgument('--print-api-key', action='store_true',
                     help='Print the created API key')
    def create_user(self, where, email, password, fullname, uid=None,
                    username=None, key_file=None, scm_level=None,
                    bugzilla_group=None, no_api_key=False,
                    print_api_key=False):
        mr = self._get_mozreview(where)
        u = mr.create_user(email, password, fullname,
                           uid=uid,
                           username=username,
                           key_filename=key_file,
                           scm_level=scm_level,
                           bugzilla_groups=bugzilla_group,
                           api_key=not no_api_key)
        print('Created user %s' % u['bugzilla']['id'])

        if print_api_key:
            print(u['bugzilla']['api_key'])

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

    @Command('create-api-key', category='mozreview',
             description='Create a Bugzilla API key for a user')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    @CommandArgument('email',
                     help='Bugzilla account to create API key for')
    def create_api_key(self, where, email):
        mr = self._get_mozreview(where)
        print(mr.create_user_api_key(email, sync_to_reviewboard=False))

    @Command('exec', category='mozreview',
             description='Execute a command in a Docker container')
    @CommandArgument('name', help='Name of container to shell into',
                     choices={'bmoweb', 'bmodb', 'pulse', 'rbweb', 'hgrb',
                              'autoland', 'hgweb', 'treestatus'})
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
                              'autoland', 'treestatus'})
    def shell(self, name):
        return self.execute(name, ['/bin/bash'])

    @Command('use-local-reviewboard', category='mozreview',
             description='Replace version of reviewboard on rbweb container '
                         'with version from specified path')
    @CommandArgument('where', nargs='?',
                     help='Directory of MozReview instance')
    @CommandArgument('path', help='Relative path of repository')
    def use_local_reviewboard(self, where, path):
        import glob
        import tarfile

        # TODO: We should automatically determine the version of python on
        #       rbweb and attempt to build using the same version, rather than
        #       hard coding the destination and building with the system
        #       python.
        # TODO: We should also make it possible to update djblets, either from
        #       this command or through another one.
        # TODO: This whole thing is a bit of a hack, use at your own risk.
        rbweb_site_packages = '/venv/lib/python2.6/site-packages'

        print('building reviewboard package')
        subprocess.check_call(['python', 'setup.py', 'build'], cwd=path)
        built_path = glob.glob(os.path.join(path, 'build', 'lib*'))[0]
        cwd = os.getcwd()
        os.chdir(built_path)
        with tarfile.open(os.path.join(cwd, 'rb.tgz'), 'w|gz') as tar:
            tar.add('reviewboard')
        os.chdir(cwd)

        mr = self._get_mozreview(where)

        print('copying files to rbweb container')
        subprocess.check_call('docker cp rb.tgz %s:rb.tgz' % mr.rbweb_id,
                              shell=True)
        subprocess.check_call('docker exec %s tar -C %s -zxf /rb.tgz' % (
                              mr.rbweb_id, rbweb_site_packages),
                              shell=True)

        print('restarting rbweb container')
        subprocess.check_call('docker exec %s /kill-wsgi-procs' % mr.rbweb_id,
                              shell=True)
