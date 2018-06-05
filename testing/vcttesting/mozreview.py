# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function

import errno
import json
import logging
import os
import subprocess
import time

import concurrent.futures as futures
import requests

from vcttesting.bugzilla import Bugzilla
from vcttesting.docker import (
    Docker,
    DockerNotAvailable,
    params_from_env,
)
from vcttesting.reviewboard import MozReviewBoard

from .ldap import LDAP
from .util import get_available_port, limited_threadpoolexecutor

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

# Allow reviewboard-fork to easily detect when running within the dev env.
os.putenv('MOZREVIEW_DEV', '1')


class MozReview(object):
    """Interface to MozService service.

    This class can be used to create and control MozReview instances.
    """

    def __init__(self, path, web_image=None, hgrb_image=None,
                 ldap_image=None, pulse_image=None, rbweb_image=None,
                 hgweb_image=None, treestatus_image=None):
        if not path:
            raise Exception('You must specify a path to create an instance')
        path = os.path.abspath(path)
        self._path = path

        self.started = False

        self.web_image = web_image
        self.hgrb_image = hgrb_image
        self.ldap_image = ldap_image
        self.pulse_image = pulse_image
        self.rbweb_image = rbweb_image
        self.hgweb_image = hgweb_image
        self.treestatus_image = treestatus_image

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

        docker_state = os.path.join(path, '.dockerstate')

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
              web_image=None, hgrb_image=None,
              ldap_image=None, ldap_port=None, pulse_image=None,
              rbweb_image=None, ssh_port=None,
              hgweb_image=None, hgweb_port=None,
              treestatus_image=None, treestatus_port=None, max_workers=None):
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
        if not hgweb_port:
            hgweb_port = get_available_port()
        if not treestatus_port:
            treestatus_port = get_available_port()

        web_image = web_image or self.web_image
        hgrb_image = hgrb_image or self.hgrb_image
        ldap_image = ldap_image or self.ldap_image
        pulse_image = pulse_image or self.pulse_image
        rbweb_image = rbweb_image or self.rbweb_image
        hgweb_image = hgweb_image or self.hgweb_image
        treestatus_image = treestatus_image or self.treestatus_image

        if not os.path.exists(os.path.join(ROOT, 'reviewboard-fork')):
            raise Exception('Failed to find reviewboard-fork. '
                            'Please run create-test-environment.')

        self.started = True
        mr_info = self._docker.start_mozreview(
                cluster=self._name,
                http_port=bugzilla_port,
                pulse_port=pulse_port,
                web_image=web_image,
                hgrb_image=hgrb_image,
                ldap_image=ldap_image,
                ldap_port=ldap_port,
                pulse_image=pulse_image,
                rbweb_image=rbweb_image,
                rbweb_port=reviewboard_port,
                ssh_port=ssh_port,
                hg_port=mercurial_port,
                hgweb_image=hgweb_image,
                hgweb_port=hgweb_port,
                treestatus_image=treestatus_image,
                treestatus_port=treestatus_port,
                max_workers=max_workers,
                verbose=verbose)

        self.bmoweb_id = mr_info['web_id']

        self.bugzilla_url = mr_info['bugzilla_url']
        bugzilla = self.get_bugzilla()

        self.reviewboard_url = mr_info['reviewboard_url']
        self.rbweb_id = mr_info['rbweb_id']

        self.pulse_id = mr_info['pulse_id']
        self.pulse_host = mr_info['pulse_host']
        self.pulse_port = mr_info['pulse_port']

        self.admin_username = bugzilla.username
        self.admin_password = bugzilla.password
        self.hg_rb_username = "mozreview"
        self.hg_rb_email = "mozreview@example.com"
        self.hg_rb_password = "mrpassword"
        self.ldap_uri = mr_info['ldap_uri']
        self.hgrb_id = mr_info['hgrb_id']
        self.ssh_hostname = mr_info['ssh_hostname']
        self.ssh_port = mr_info['ssh_port']
        self.mercurial_url = mr_info['mercurial_url']
        self.hgweb_id = mr_info['hgweb_id']
        self.hgweb_url = mr_info['hgweb_url']

        self.treestatus_id = mr_info['treestatus_id']
        self.treestatus_url = mr_info['treestatus_url']

        rb = self.get_reviewboard()

        # It is tempting to put the user creation inside the futures
        # block so it runs concurrently. However, there appeared to be
        # race conditions here. The hg_rb_username ("mozreview") user
        # was sometimes not getting created and this led to intermittent
        # test failures in test-auth.t.

        # Ensure admin user is present.
        rb.login_user(bugzilla.username, bugzilla.password)

        # Ensure the mozreview hg user is present and has privileges.
        # This has to occur after the admin user is logged in to avoid
        # race conditions with user IDs.
        rb.create_local_user(self.hg_rb_username, self.hg_rb_email,
                             self.hg_rb_password)

        with limited_threadpoolexecutor(7, max_workers) as e:
            # Ensure admin user had admin privileges.
            e.submit(rb.make_admin, bugzilla.username)

            # Ensure mozreview user has permissions for testing.
            e.submit(rb.grant_permission, self.hg_rb_username,
                     'Can change ldap assocation for all users')

            e.submit(rb.grant_permission, self.hg_rb_username,
                     'Can verify DiffSet legitimacy')

            e.submit(rb.grant_permission, self.hg_rb_username,
                     'Can enable or disable autoland for a repository')

            # Tell hgrb about URLs.
            e.submit(self._docker.execute, self.hgrb_id,
                     ['/set-urls', self.bugzilla_url, self.reviewboard_url])

            # Define site domain and hostname in rbweb. This is necessary so it
            # constructs self-referential URLs properly.
            e.submit(self._docker.execute, self.rbweb_id,
                     ['/set-site-url', self.reviewboard_url, self.bugzilla_url])

            # Tell Bugzilla about Review Board URL.
            e.submit(self._docker.execute, mr_info['web_id'],
                     ['/set-urls', self.reviewboard_url])

        self.create_user_api_key(bugzilla.username, description='mozreview')

        with futures.ThreadPoolExecutor(2) as e:
            f_ssh_ed25519_key = e.submit(self._docker.get_file_content,
                                         mr_info['hgrb_id'],
                                         '/etc/mercurial/ssh/ssh_host_ed25519_key.pub')
            f_ssh_rsa_key = e.submit(self._docker.get_file_content,
                                     mr_info['hgrb_id'],
                                     '/etc/mercurial/ssh/ssh_host_rsa_key.pub')

        ssh_ed25519_key = f_ssh_ed25519_key.result().split()[0:2]
        ssh_rsa_key = f_ssh_rsa_key.result().split()[0:2]

        hostkeys_path = os.path.join(self._path, 'ssh-known-hosts')
        hoststring = '[%s]:%d' % (mr_info['ssh_hostname'], mr_info['ssh_port'])
        with open(hostkeys_path, 'wb') as fh:
            fh.write('%s %s %s\n' % (hoststring, ssh_ed25519_key[0], ssh_ed25519_key[1]))
            fh.write('%s %s %s\n' % (hoststring, ssh_rsa_key[0], ssh_rsa_key[1]))

        with open(os.path.join(self._path, 'ssh_config'), 'wb') as fh:
            fh.write(SSH_CONFIG.format(
                known_hosts=hostkeys_path,
                hostname=self.ssh_hostname,
                port=self.ssh_port))

        state = {
            'bmoweb_id': self.bmoweb_id,
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
            'hgrb_id': self.hgrb_id,
            'hgweb_url': self.hgweb_url,
            'hgweb_id': self.hgweb_id,
            'ssh_hostname': self.ssh_hostname,
            'ssh_port': self.ssh_port,
            'treestatus_url': self.treestatus_url,
            'treestatus_id': self.treestatus_id,
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

    def refresh(self, verbose=False, refresh_reviewboard=False):
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
                res = self._docker.execute(cid, command, stream=True,
                                           stderr=verbose, stdout=verbose)
                for msg in res:
                    if verbose:
                        msg = msg.rstrip().lstrip('\n')
                        for line in msg.splitlines():
                            if line != '':
                                print('%s> %s' % (name, line))

            def refresh(name, cid):
                execute(name, cid, ['/refresh', url,
                                    'all' if refresh_reviewboard else ''])

            with futures.ThreadPoolExecutor(4) as e:
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

        expression = [
            'anyof',
            ['dirname', 'hgext/reviewboard'],
            ['dirname', 'pylib/mozreview'],
            ['dirname', 'pylib/reviewboardmods'],
            ['dirname', 'reviewboard-fork/djblets'],
            ['dirname', 'reviewboard-fork/reviewboard'],
        ]
        command = ['%s/scripts/watchman-refresh-wrapper' % ROOT, ROOT,
                   self._path]
        data = json.dumps(['trigger', ROOT, {
            'name': name,
            'chdir': ROOT,
            'expression': expression,
            'command': command,
            'append_files': True,
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

        self._docker.execute(self.hgrb_id,
                            ['/create-repo', name, str(rbid)])

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
                             bugzilla_apikey=None):
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
                                        bugzilla_apikey=bugzilla_apikey)

    def create_user_api_key(self, email, sync_to_reviewboard=True,
                            description=''):
        """Creates an API key for the given user.

        This creates an API key in Bugzilla and then triggers the
        auth-delegation callback to register the key with Review Board. Note
        that this also logs the user in, although we don't record the session
        cookie anywhere so this shouldn't have an effect on subsequent
        interactions with Review Board.
        """
        api_key = self._docker.execute(
            self.bmoweb_id,
            ['/var/lib/bugzilla/bugzilla/scripts/issue-api-key.pl',
             email, description], stdout=True).strip()

        assert len(api_key) == 40

        if not sync_to_reviewboard:
            return api_key

        # When running tests in parallel, the auth callback can time out.
        # Try up to 3 times before giving up.
        url = self.reviewboard_url + 'mozreview/bmo_auth_callback/'
        data = {'client_api_login': email, 'client_api_key': api_key}

        for i in range(3):
            response = requests.post(url, data=json.dumps(data))
            if response.status_code == 200:
                result = response.json()['result']
                break
        else:
            raise Exception('Failed to successfully run the BMO auth POST '
                            'callback.')

        params = {
            'client_api_login': email,
            'callback_result': result,
            'secret': 'mozreview',
        }
        cookies = {'bmo_auth_secret': params['secret']}

        for i in range(3):
            if requests.get(url, params=params,
                            cookies=cookies).status_code == 200:
                break
        else:
            raise Exception('Failed to successfully run the BMO auth GET '
                            'callback.')

        return api_key

    def create_user(self, email, password, fullname, bugzilla_groups=None,
                    uid=None, username=None, key_filename=None, scm_level=None,
                    api_key=True, bugzilla_email=None):
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
        ``key_filename`` is a path to an ssh key. This is used only if ``uid``
        is given. If ``uid`` is given but ``key_filename`` is not specified,
        the latter defaults to <mozreview path>/keys/<email>.
        ``scm_level`` defines the source code level access to grant to this
        user. Supported levels are ``1``, ``2``, and ``3``. If not specified,
        the user won't be able to push to any repos.
        ``bugzilla_email`` set the bugzillaEmail LDAP attribute to this instead
        of ``email``.
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

        if api_key:
            res['bugzilla']['api_key'] = self.create_user_api_key(
                email, description='mozreview')

        # Create an LDAP account as well.
        if uid:
            if key_filename is None:
                key_filename = os.path.join(self._path, 'keys', email)

            lr = self.get_ldap().create_user(email, username, uid,
                                             fullname,
                                             key_filename=key_filename,
                                             scm_level=scm_level,
                                             bugzilla_email=bugzilla_email)

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
                 ircnick=None, bugzilla_username=None, bugzilla_apikey=None):
        """Create a local Mercurial repository.

        ``mrpath`` is the home directory of the MozReview installation.
        ``hg`` is the hg binary to use.
        ``path`` is the local path to initialize the repository at.
        ``default_url`` is the URL for the default path to the repository.
        ``push_url`` is the default URL to be used for pushing.
        ``ircnick`` is the IRC nickname to use.
        ``bugzilla_username`` and ``bugzilla_apikey`` define the credentials
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

            if bugzilla_username or bugzilla_apikey:
                fh.write('[bugzilla]\n')
                if bugzilla_username:
                    fh.write('username = %s\n' % bugzilla_username)
                if bugzilla_apikey:
                    fh.write('apikey = %s\n' % bugzilla_apikey)
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
                '[reviewboard]',
                'autopublish = false',
                '',
            ]))

    def run(self, args):
        cmd = [self.hg, '--config', 'ui.interactive=false']
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
