# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function

import errno
import json
import logging
import os
import subprocess

import paramiko
import concurrent.futures as futures

from vcttesting.bugzilla import Bugzilla
from vcttesting.docker import (
    Docker,
    DockerNotAvailable,
    params_from_env,
)
from vcttesting.reviewboard import MozReviewBoard

from .ldap import LDAP
from .util import get_available_port

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


SSH_CONFIG = '''
Host *
  StrictHostKeyChecking no
  PasswordAuthentication no
  PreferredAuthentications publickey
  UserKnownHostsFile {known_hosts}
  ForwardX11 no

Host hgrb
  HostName {hostname}
  Port {port}
'''.strip()


logger = logging.getLogger(__name__)


WATCHMAN = None
for path in os.environ['PATH'].split(':'):
    c = os.path.join(path, 'watchman')
    if os.path.exists(c):
        WATCHMAN = c
        break


class MozReview(object):
    """Interface to MozService service.

    This class can be used to create and control MozReview instances.
    """

    def __init__(self, path, web_image=None, db_image=None, hgrb_image=None,
                 ldap_image=None, pulse_image=None, rbweb_image=None,
                 autolanddb_image=None, autoland_image=None):
        if not path:
            raise Exception('You must specify a path to create an instance')
        path = os.path.abspath(path)
        self._path = path

        self.started = False

        self.db_image = db_image
        self.web_image = web_image
        self.hgrb_image = hgrb_image
        self.ldap_image = ldap_image
        self.pulse_image = pulse_image
        self.rbweb_image = rbweb_image
        self.autolanddb_image = autolanddb_image
        self.autoland_image = autoland_image

        self._name = os.path.dirname(path)

        if not os.path.exists(path):
            os.mkdir(path)

        keys_path = os.path.join(path, 'keys')
        try:
            os.mkdir(keys_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        credentials_path = os.path.join(path, 'credentials')
        try:
            os.mkdir(credentials_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        self._state_path = os.path.join(path, 'state.json')

        docker_state = os.path.join(path, 'docker-state.json')

        self._docker_state = docker_state

        self.bugzilla_username = None
        self.bugzilla_password = None
        self.docker_env = {}

        if os.path.exists(self._state_path):
            with open(self._state_path, 'rb') as fh:
                state = json.load(fh)

                for k, v in state.items():
                    setattr(self, k, v)

        # Preserve Docker settings from last time.
        #
        # This was introduced to make watchman happy, as its triggers may not
        # inherit environment variables.
        for k, v in self.docker_env.items():
            os.environ[k] = v

        docker_url, tls = params_from_env(os.environ)
        self._docker = Docker(docker_state, docker_url, tls=tls)

        if not self._docker.is_alive():
            raise DockerNotAvailable('Docker is not available.')

    def get_bugzilla(self, username=None, password=None):
        username = username or self.bugzilla_username or 'admin@example.com'
        password = password or self.bugzilla_password or 'password'

        return Bugzilla(self.bugzilla_url, username=username, password=password)

    def get_reviewboard(self):
        """Obtain a MozReviewBoard instance tied to this MozReview instance."""
        return MozReviewBoard(self._docker, self.rbweb_id,
                              self.reviewboard_url,
                              bugzilla_url=self.bugzilla_url,
                              pulse_host=self.pulse_host,
                              pulse_port=self.pulse_port)

    def get_ldap(self):
        """Obtain an LDAP instance connected to the LDAP server in this instance."""
        return LDAP(self.ldap_uri, 'cn=admin,dc=mozilla', 'password')

    def start(self, bugzilla_port=None, reviewboard_port=None,
            mercurial_port=None, pulse_port=None, verbose=False,
            db_image=None, web_image=None, hgrb_image=None,
            ldap_image=None, ldap_port=None, pulse_image=None,
            rbweb_image=None, ssh_port=None,
            autolanddb_image=None, autoland_image=None, autoland_port=None):
        """Start a MozReview instance."""
        if self.started:
            raise Exception('MozReview instance has already been started')

        if not bugzilla_port:
            bugzilla_port = get_available_port()
        if not reviewboard_port:
            reviewboard_port = get_available_port()
        if not mercurial_port:
            mercurial_port = get_available_port()
        if not ldap_port:
            ldap_port = get_available_port()
        if not ssh_port:
            ssh_port = get_available_port()
        if not pulse_port:
            pulse_port = get_available_port()
        if not autoland_port:
            autoland_port = get_available_port()

        db_image = db_image or self.db_image
        web_image = web_image or self.web_image
        hgrb_image = hgrb_image or self.hgrb_image
        ldap_image = ldap_image or self.ldap_image
        pulse_image = pulse_image or self.pulse_image
        rbweb_image = rbweb_image or self.rbweb_image
        autolanddb_image = autolanddb_image or self.autolanddb_image
        autoland_image = autoland_image or self.autoland_image

        self.started = True
        mr_info = self._docker.start_mozreview(
                cluster=self._name,
                http_port=bugzilla_port,
                pulse_port=pulse_port,
                db_image=db_image,
                web_image=web_image,
                hgrb_image=hgrb_image,
                ldap_image=ldap_image,
                ldap_port=ldap_port,
                pulse_image=pulse_image,
                rbweb_image=rbweb_image,
                rbweb_port=reviewboard_port,
                ssh_port=ssh_port,
                hg_port=mercurial_port,
                autolanddb_image=autolanddb_image,
                autoland_image=autoland_image,
                autoland_port=autoland_port,
                verbose=verbose)

        self.bmoweb_id = mr_info['web_id']
        self.bmodb_id = mr_info['db_id']

        self.bugzilla_url = mr_info['bugzilla_url']
        bugzilla = self.get_bugzilla()

        self.reviewboard_url = mr_info['reviewboard_url']
        self.rbweb_id = mr_info['rbweb_id']

        self.autoland_id = mr_info['autoland_id']
        self.autoland_url = mr_info['autoland_url']
        self.pulse_id = mr_info['pulse_id']
        self.pulse_host = mr_info['pulse_host']
        self.pulse_port = mr_info['pulse_port']

        self.admin_username = bugzilla.username
        self.admin_password = bugzilla.password
        self.hg_rb_username = "mozreview"
        self.hg_rb_email = "mozreview@example.com"
        self.hg_rb_password = "password"
        self.ldap_uri = mr_info['ldap_uri']
        self.hgrb_id = mr_info['hgrb_id']
        self.ssh_hostname = mr_info['ssh_hostname']
        self.ssh_port = mr_info['ssh_port']
        self.mercurial_url = mr_info['mercurial_url']

        # Ensure admin user is present and has admin privileges.
        def make_users():
            rb = self.get_reviewboard()

            # Ensure admin user is present and has admin privileges.
            rb.login_user(bugzilla.username, bugzilla.password)
            rb.make_admin(bugzilla.username)

            # Ensure the MozReview hg user is present and has privileges.
            rb.create_local_user(self.hg_rb_username, self.hg_rb_email,
                                 self.hg_rb_password)
            rb.grant_permission(self.hg_rb_username,
                                'Can change ldap assocation for all users')



        with futures.ThreadPoolExecutor(4) as e:
            e.submit(make_users)

            # Tell hgrb about URLs.
            e.submit(self._docker.client.execute, self.hgrb_id,
                     ['/set-urls', self.bugzilla_url, self.reviewboard_url])

            # Define site domain and hostname in rbweb. This is necessary so it
            # constructs self-referential URLs properly.
            e.submit(self._docker.client.execute, self.rbweb_id,
                     ['/set-site-url', self.reviewboard_url])

            # Tell Bugzilla about Review Board URL.
            e.submit(self._docker.client.execute, mr_info['web_id'],
                     ['/set-urls', self.reviewboard_url])

        hg_ssh_host_key = self._docker.get_file_content(
                mr_info['hgrb_id'],
                '/etc/ssh/ssh_host_rsa_key.pub').rstrip()
        key_type, key_key = hg_ssh_host_key.split()

        assert key_type == 'ssh-rsa'
        key = paramiko.rsakey.RSAKey(data=paramiko.py3compat.decodebytes(key_key))

        hostkeys_path = os.path.join(self._path, 'ssh-known-hosts')
        load_path = hostkeys_path if os.path.exists(hostkeys_path) else None
        hostkeys = paramiko.hostkeys.HostKeys(filename=load_path)
        hoststring = '[%s]:%d' % (mr_info['ssh_hostname'], mr_info['ssh_port'])
        hostkeys.add(hoststring, key_type, key)
        hostkeys.save(hostkeys_path)

        with open(os.path.join(self._path, 'ssh_config'), 'wb') as fh:
            fh.write(SSH_CONFIG.format(
                known_hosts=hostkeys_path,
                hostname=self.ssh_hostname,
                port=self.ssh_port))

        state = {
            'bmoweb_id': self.bmoweb_id,
            'bmodb_id': self.bmodb_id,
            'bugzilla_url': self.bugzilla_url,
            'reviewboard_url': self.reviewboard_url,
            'rbweb_id': self.rbweb_id,
            'mercurial_url': self.mercurial_url,
            'admin_username': bugzilla.username,
            'admin_password': bugzilla.password,
            'ldap_uri': self.ldap_uri,
            'pulse_id': self.pulse_id,
            'pulse_host': self.pulse_host,
            'pulse_port': self.pulse_port,
            'autoland_url': self.autoland_url,
            'autoland_id': self.autoland_id,
            'hgrb_id': self.hgrb_id,
            'ssh_hostname': self.ssh_hostname,
            'ssh_port': self.ssh_port,
            'docker_env': {k: v for k, v in os.environ.items() if k.startswith('DOCKER')}
        }

        with open(self._state_path, 'wb') as fh:
            json.dump(state, fh, indent=2, sort_keys=True)

    def stop(self):
        """Stop all services associated with this MozReview instance."""
        self._docker.stop_bmo(self._name)
        self.started = False

        if WATCHMAN:
            with open(os.devnull, 'wb') as devnull:
                subprocess.call([WATCHMAN, 'trigger-del', ROOT,
                                 'mozreview-%s' % os.path.basename(self._path)],
                                stdout=devnull, stderr=subprocess.STDOUT)

    def refresh(self, verbose=False):
        """Refresh a running cluster with latest version of code.

        This only updates code from the v-c-t repo. Not all containers
        are currently updated.
        """
        with self._docker.vct_container(verbose=verbose) as vct_state:
            # We update rbweb by rsyncing state and running the refresh script.
            rsync_port = vct_state['NetworkSettings']['Ports']['873/tcp'][0]['HostPort']
            url = 'rsync://%s:%s/vct-mount/' % (self._docker.docker_hostname,
                                                rsync_port)

            def execute(name, cid, command):
                res = self._docker.client.execute(cid, command, stream=True)
                for msg in res:
                    if verbose:
                        print('%s> %s' % (name, msg), end='')

            def refresh(name, cid):
                execute(name, cid, ['/refresh', url])

            with futures.ThreadPoolExecutor(3) as e:
                e.submit(refresh, 'rbweb', self.rbweb_id)
                e.submit(refresh, 'hgrb', self.hgrb_id)
                e.submit(execute, 'bmoweb', self.bmoweb_id,
                         ['/usr/bin/supervisorctl', 'restart', 'httpd'])

    def start_autorefresh(self):
        """Enable auto refreshing of the cluster when changes are made.

        Watchman will be configured to start watching the source directory.
        When relevant files are changed, containers will be synchronized
        automatically.

        When enabled, this removes overhead from developers having to manually
        refresh state during development.
        """
        if not WATCHMAN:
            raise Exception('watchman binary not found')
        subprocess.check_call([WATCHMAN, 'watch-project', ROOT])
        name = 'mozreview-%s' % os.path.basename(self._path)

        data = json.dumps(['trigger', ROOT, {
            'name': name,
            'chdir': ROOT,
            'expression': ['anyof',
                ['dirname', 'hgext/reviewboard'],
                ['dirname', 'pylib/mozreview'],
                ['dirname', 'pylib/rbbz'],
                ['dirname', 'reviewboardmods'],
            ],
            'command': ['%s/mozreview' % ROOT, 'refresh', self._path],
        }])
        p = subprocess.Popen([WATCHMAN, '-j'], stdin=subprocess.PIPE)
        p.communicate(data)
        res = p.wait()
        if res != 0:
            raise Exception('error creating watchman trigger')

    def repo_urls(self, name):
        """Obtain the http:// and ssh:// URLs for a review repo."""
        http_url = '%s%s' % (self.mercurial_url, name)
        ssh_url = 'ssh://%s:%d/%s' % (self.ssh_hostname, self.ssh_port, name)

        return http_url, ssh_url

    def create_repository(self, name):
        http_url, ssh_url = self.repo_urls(name)

        rb = self.get_reviewboard()
        rbid = rb.add_repository(os.path.dirname(name) or name, http_url,
                                 bugzilla_url=self.bugzilla_url)

        self._docker.client.execute(self.hgrb_id,
                                    ['/create-repo', name, str(rbid)])

        if self.autoland_id:
            self._docker.client.execute(self.autoland_id, ['/clone-repo',
                                        name])

        return http_url, ssh_url, rbid

    def clone(self, repo, dest, username=None):
        """Clone and configure a review repository.

        The specified review repo will be cloned and configured such that it is
        bound to this MozReview instance. If a username is specified, all
        operations will be performed as that user.
        """
        http_url, ssh_url = self.repo_urls(repo)

        subprocess.check_call([self._hg, 'clone', http_url, dest], cwd='/')

        mrext = os.path.join(ROOT, 'testing', 'mozreview-repo.py')
        mrssh = os.path.join(ROOT, 'testing', 'mozreview-ssh')
        rbext = os.path.join(ROOT, 'hgext', 'reviewboard', 'client.py')

        with open(os.path.join(dest, '.hg', 'hgrc'), 'w') as fh:
            lines = [
                '[paths]',
                'default = %s' % http_url,
                'default-push = %s' % ssh_url,
                '',
                '[extensions]',
                'mozreview-repo = %s' % mrext,
                'reviewboard = %s' % rbext,
                '',
                '[ui]',
                'ssh = %s' % mrssh,
                '',
                # TODO use ircnick from the current user, if available.
                '[mozilla]',
                'ircnick = dummy',
                '',
                '[mozreview]',
                'home = %s' % self._path,
            ]

            if username:
                lines.append('username = %s' % username)

            fh.write('\n'.join(lines))
            fh.write('\n')

    def get_local_repository(self, path, ircnick=None,
                             bugzilla_username=None,
                             bugzilla_password=None):
        """Obtain a LocalMercurialRepository for the named server repository.

        Call this with the same argument passed to ``create_repository()``
        to obtain an object to interface with a local clone of that server
        repository.

        If bugzilla credentials are passed, they will be defined in the
        repository's hgrc.

        The repository is configured to be in deterministic mode. Therefore
        these repositories are suitable for use in tests.
        """
        localrepos = os.path.join(self._path, 'localrepos')
        try:
            os.mkdir(localrepos)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        local_path = os.path.join(localrepos, os.path.basename(path))

        http_url, ssh_url = self.repo_urls(path)

        # TODO make pushes via SSH work (it doesn't work outside of Mercurial
        # tests because dummy expects certain environment variables).
        return LocalMercurialRepository(self._path, self._hg, local_path,
                                        http_url, push_url=ssh_url, ircnick=ircnick,
                                        bugzilla_username=bugzilla_username,
                                        bugzilla_password=bugzilla_password)

    def create_user(self, email, password, fullname, bugzilla_groups=None,
                    uid=None, username=None, scm_level=None):
        """Create a new user.

        This will create a user in at least Bugzilla. If the ``uid`` argument
        is specified, an LDAP user will be created as well.

        ``email`` is the email address of the user.
        ``password`` is the plain text Bugzilla password.
        ``fullname`` is the full name of the user. This is stored in both
        Bugzilla and the system account for the user (if an LDAP user is being
        created).
        ``bugzilla_groups`` is an iterable of Bugzilla groups to add the user
        to.
        ``uid`` is the numeric UID for the created system/LDAP account.
        ``username`` is the UNIX username for this user. It defaults to the
        username part of the email address.
        ``scm_level`` defines the source code level access to grant to this
        user. Supported levels are ``1``, ``2``, and ``3``. If not specified,
        the user won't be able to push to any repos.
        """
        bugzilla_groups = bugzilla_groups or []

        b = self.get_bugzilla()

        if not username:
            username = email[0:email.index('@')]

        res = {
            'bugzilla': b.create_user(email, password, fullname),
        }

        for g in bugzilla_groups:
            b.add_user_to_group(email, g)

        # Create an LDAP account as well.
        if uid:
            key_filename = os.path.join(self._path, 'keys', email)
            lr = self.get_ldap().create_user(email, username, uid,
                                             fullname,
                                             key_filename=key_filename,
                                             scm_level=scm_level)

            res.update(lr)

        credentials_path = os.path.join(self._path, 'credentials', email)
        with open(credentials_path, 'wb') as fh:
            fh.write(password)

        return res

    @property
    def _hg(self):
        for path in os.environ['PATH'].split(os.pathsep):
            hg = os.path.join(path, 'hg')
            if os.path.isfile(hg):
                return hg

        raise Exception('could not find hg executable')


class LocalMercurialRepository(object):
    """An interface to a Mercurial repository on the local filesystem.

    This class facilitates easily running ``hg`` commands against a local
    repository from the context of Python.
    """
    def __init__(self, mrpath, hg, path, default_url, push_url=None,
                 ircnick=None, bugzilla_username=None, bugzilla_password=None):
        """Create a local Mercurial repository.

        ``mrpath`` is the home directory of the MozReview installation.
        ``hg`` is the hg binary to use.
        ``path`` is the local path to initialize the repository at.
        ``default_url`` is the URL for the default path to the repository.
        ``push_url`` is the default URL to be used for pushing.
        ``ircnick`` is the IRC nickname to use.
        ``bugzilla_username`` and ``bugzilla_password`` define the credentials
        to use when talking to Bugzilla or MozReview.
        """
        self.mrpath = mrpath
        self.hg = hg
        self.path = path
        self.bugzilla_username = bugzilla_username

        if not os.path.exists(path):
            subprocess.check_call([self.hg, 'init', path], cwd='/')

        mrssh = os.path.join(ROOT, 'testing', 'mozreview-ssh')
        reviewboard = os.path.join(ROOT, 'hgext', 'reviewboard', 'client.py')

        with open(os.path.join(path, '.hg', 'hgrc'), 'w') as fh:
            fh.write('\n'.join([
                '[paths]',
                'default = %s\n' % default_url,
            ]))
            if push_url:
                fh.write('default-push = %s\n' % push_url)
            fh.write('\n')

            if bugzilla_username or bugzilla_password:
                fh.write('[bugzilla]\n')
                if bugzilla_username:
                    fh.write('username = %s\n' % bugzilla_username)
                if bugzilla_password:
                    fh.write('password = %s\n' % bugzilla_password)
                fh.write('\n')

            if ircnick:
                fh.write('[mozilla]\n')
                fh.write('ircnick = %s\n' % ircnick)
                fh.write('\n')

            fh.write('\n'.join([
                '[ui]',
                'ssh = %s' % mrssh,
                '',
                '[defaults]',
                'backout = -d "0 0"',
                'commit = -d "0 0"',
                'shelve = --date "0 0"',
                'tag = -d "0 0"',
                '',
                '[extensions]',
                'reviewboard = %s' % reviewboard,
                '',
            ]))

    def run(self, args):
        cmd = [self.hg]
        cmd.extend(args)

        env = dict(os.environ)
        env['HGUSER'] = 'test'
        env['EMAIL'] = 'Foo Bar <foo.bar@example.com>'
        env['HOME'] = '/'
        env['TZ'] = 'GMT'
        env['LANG'] = env['LC_ALL'] = env['LANGUAGE'] = 'C'
        env['HGENCODING'] = 'ascii'

        # Needed so SSH wrapper picks the right key.
        if self.bugzilla_username:
            env['MOZREVIEW_HOME'] = self.mrpath
            env['SSH_KEYNAME'] = self.bugzilla_username

        try:
            logger.info('Running command: %s' % cmd)
            return subprocess.check_output(cmd, cwd=self.path,
                                           stderr=subprocess.STDOUT,
                                           env=env)
        except subprocess.CalledProcessError as e:
            logger.error('Error running command: %s' % e.output)
            raise

    def touch(self, path):
        p = os.path.join(self.path, path)
        with open(p, 'a'):
            os.utime(p, None)

    def write(self, path, content):
        with open(os.path.join(self.path, path), 'w') as fh:
            fh.write(content)

    def append(self, path, content):
        with open(os.path.join(self.path, path), 'a') as fh:
            fh.write(content)
