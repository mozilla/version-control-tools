# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import errno
import json
import os
import subprocess
import urlparse

import concurrent.futures as futures

from vcttesting.bugzilla import Bugzilla
from vcttesting.docker import (
    Docker,
    params_from_env,
)
from vcttesting.reviewboard import MozReviewBoard

from .util import (
    get_available_port,
    kill,
)

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


class MozReview(object):
    """Interface to MozService service.

    This class can be used to create and control MozReview instances.
    """

    def __init__(self, path, web_image=None, db_image=None, ldap_image=None,
                 pulse_image=None, autolanddb_image=None, autoland_image=None):
        if not path:
            raise Exception('You must specify a path to create an instance')
        path = os.path.abspath(path)
        self._path = path

        self.db_image = db_image
        self.web_image = web_image
        self.ldap_image = ldap_image
        self.pulse_image = pulse_image
        self.autolanddb_image = autolanddb_image
        self.autoland_image = autoland_image

        self._name = os.path.dirname(path)

        if not os.path.exists(path):
            os.mkdir(path)

        self._state_path = os.path.join(path, 'state.json')

        docker_state = os.path.join(path, 'docker-state.json')

        self._docker_state = docker_state

        docker_url, tls = params_from_env(os.environ)
        self._docker = Docker(docker_state, docker_url, tls=tls)

        if not self._docker.is_alive():
            raise Exception('Docker is not available.')

        self.bugzilla_username = None
        self.bugzilla_password = None

        if os.path.exists(self._state_path):
            with open(self._state_path, 'rb') as fh:
                state = json.load(fh)

                for k, v in state.items():
                    setattr(self, k, v)

    def get_bugzilla(self, username=None, password=None):
        username = username or self.bugzilla_username or 'admin@example.com'
        password = password or self.bugzilla_password or 'password'

        return Bugzilla(self.bugzilla_url, username=username, password=password)

    def get_reviewboard(self):
        """Obtain a MozReviewBoard instance tied to this MozReview instance."""
        return MozReviewBoard(self._path,
                              bugzilla_url=self.bugzilla_url,
                              pulse_host=self.pulse_host,
                              pulse_port=self.pulse_port)

    def restart_reviewboard(self):
        rb = self.get_reviewboard()
        rb.stop()

        url = urlparse.urlparse(self.reviewboard_url)
        rb.start(url.port)

        return self.reviewboard_url


    def start(self, bugzilla_port=None, reviewboard_port=None,
            mercurial_port=None, pulse_port=None, verbose=False,
            db_image=None, web_image=None, ldap_image=None, ldap_port=None,
            pulse_image=None,
            autolanddb_image=None, autoland_image=None, autoland_port=None):
        """Start a MozReview instance."""
        if not bugzilla_port:
            bugzilla_port = get_available_port()
        if not reviewboard_port:
            reviewboard_port = get_available_port()
        if not mercurial_port:
            mercurial_port = get_available_port()
        if not ldap_port:
            ldap_port = get_available_port()
        if not pulse_port:
            pulse_port = get_available_port()
        if not autoland_port:
            autoland_port = get_available_port()

        db_image = db_image or self.db_image
        web_image = web_image or self.web_image
        ldap_image = ldap_image or self.ldap_image
        pulse_image = pulse_image or self.pulse_image
        autolanddb_image = autolanddb_image or self.autolanddb_image
        autoland_image = autoland_image or self.autoland_image

        rb = MozReviewBoard(self._path)

        with futures.ThreadPoolExecutor(2) as e:
            f_mr_info = e.submit(self._docker.start_mozreview,
                                 cluster=self._name,
                                 hostname=None,
                                 http_port=bugzilla_port,
                                 pulse_port=pulse_port,
                                 db_image=db_image,
                                 web_image=web_image,
                                 ldap_image=ldap_image,
                                 ldap_port=ldap_port,
                                 pulse_image=pulse_image,
                                 autolanddb_image=autolanddb_image,
                                 autoland_image=autoland_image,
                                 autoland_port=autoland_port,
                                 verbose=verbose)

            e.submit(rb.create)

        mr_info = f_mr_info.result()
        rb.bugzilla_url = mr_info['bugzilla_url']
        rb.pulse_host = mr_info['pulse_host']
        rb.pulse_port = mr_info['pulse_port']

        self.bugzilla_url = mr_info['bugzilla_url']
        bugzilla = self.get_bugzilla()

        reviewboard_url = 'http://localhost:%s/' % reviewboard_port
        self.reviewboard_url = reviewboard_url

        autoland_url = 'http://localhost:%s/' % autoland_port
        self.autoland_url = autoland_url

        with futures.ThreadPoolExecutor(2) as e:
            f_rb_pid = e.submit(rb.start, reviewboard_port)
            f_hg_pid = e.submit(self._start_mercurial_server, mercurial_port)

        reviewboard_pid = f_rb_pid.result()
        self.reviewboard_pid = reviewboard_pid

        rb.make_admin(bugzilla.username)

        self.admin_username = bugzilla.username
        self.admin_password = bugzilla.password
        self.ldap_uri = mr_info['ldap_uri']
        self.pulse_host = mr_info['pulse_host']
        self.pulse_port = mr_info['pulse_port']

        mercurial_pid = f_hg_pid.result()
        self.mercurial_pid = mercurial_pid
        self.mercurial_url = 'http://localhost:%s/' % mercurial_port

        state = {
            'bugzilla_url': self.bugzilla_url,
            'reviewboard_url': reviewboard_url,
            'reviewboard_pid': reviewboard_pid,
            'mercurial_url': self.mercurial_url,
            'mercurial_pid': mercurial_pid,
            'admin_username': bugzilla.username,
            'admin_password': bugzilla.password,
            'ldap_uri': mr_info['ldap_uri'],
            'pulse_host': mr_info['pulse_host'],
            'pulse_port': mr_info['pulse_port'],
            'autoland_url': self.autoland_url,
        }

        with open(self._state_path, 'wb') as fh:
            json.dump(state, fh, indent=2, sort_keys=True)

    def stop(self):
        """Stop all services associated with this MozReview instance."""
        with futures.ThreadPoolExecutor(2) as e:
            rb = MozReviewBoard(self._path)
            e.submit(rb.stop)

            e.submit(self._docker.stop_bmo, self._name)

            if os.path.exists(self._hg_pid_path):
                with open(self._hg_pid_path, 'rb') as fh:
                    pid = int(fh.read().strip())
                    kill(pid)

                os.unlink(self._hg_pid_path)

    def create_repository(self, path):
        url = '%s%s' % (self.mercurial_url, path)
        full_path = os.path.join(self._path, 'repos', path)

        env = dict(os.environ)
        env['HGRCPATH'] = '/dev/null'
        subprocess.check_call([self._hg, 'init', full_path], env=env)

        rb = MozReviewBoard(self._path)
        rbid = rb.add_repository(os.path.dirname(path) or path, url,
                                 bugzilla_url=self.bugzilla_url)

        with open(os.path.join(full_path, '.hg', 'hgrc'), 'w') as fh:
            fh.write('\n'.join([
                '[reviewboard]',
                'repoid = %s' % rbid,
                '',
            ]))

        return url, rbid

    def get_local_repository(self, path, ircnick=None,
                             bugzilla_username=None,
                             bugzilla_password=None):
        """Obtain a LocalMercurialRepository for the named server repository.

        Call this with the same argument passed to ``create_repository()``
        to obtain an object to interface with a local clone of that server
        repository.

        If bugzilla credentials are passed, they will be defined in the
        repository's hgrc.
        """
        localrepos = os.path.join(self._path, 'localrepos')
        try:
            os.mkdir(localrepos)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        local_path = os.path.join(localrepos, os.path.basename(path))

        http_url = '%s%s' % (self.mercurial_url, path)
        ssh_url = 'ssh://user@dummy%s/localrepos/%s' % (self._path, path)

        # TODO make pushes via SSH work (it doesn't work outside of Mercurial
        # tests because dummy expects certain environment variables).
        return LocalMercurialRepository(self._hg, local_path, http_url,
                                        ircnick=ircnick,
                                        bugzilla_username=bugzilla_username,
                                        bugzilla_password=bugzilla_password)

    def create_user(self, email, password, fullname):
        b = self.get_bugzilla()
        return b.create_user(email, password, fullname)

    @property
    def _hg_pid_path(self):
        return os.path.join(self._path, 'hg.pid')

    @property
    def _hg(self):
        for path in os.environ['PATH'].split(os.pathsep):
            hg = os.path.join(path, 'hg')
            if os.path.isfile(hg):
                return hg

        raise Exception('could not find hg executable')

    def _start_mercurial_server(self, port):
        repos_path = os.path.join(self._path, 'repos')
        if not os.path.exists(repos_path):
            os.mkdir(repos_path)

        rb_ext_path = os.path.join(ROOT, 'hgext', 'reviewboard', 'server.py')
        dummyssh = os.path.join(ROOT, 'pylib', 'mercurial-support', 'dummyssh')

        global_hgrc = os.path.join(self._path, 'hgrc')
        with open(global_hgrc, 'w') as fh:
            fh.write('\n'.join([
                '[phases]',
                'publish = False',
                '',
                '[ui]',
                'ssh = python "%s"' % dummyssh,
                '',
                '[reviewboard]',
                'url = %s' % self.reviewboard_url,
                '',
                '[extensions]',
                'reviewboard = %s' % rb_ext_path,
                '',
                '[bugzilla]',
                'url = %s' % self.bugzilla_url,
                '',
            ]))

        web_conf = os.path.join(self._path, 'web.conf')
        with open(web_conf, 'w') as fh:
            fh.write('\n'.join([
                '[web]',
                'push_ssl = False',
                'allow_push = *',
                '',
                '[paths]',
                '/ = %s/**' % repos_path,
                '',
            ]))

        # hgwebdir doesn't pick up new repositories until 20s after they
        # are created. We install an extension to always refresh.
        refreshing_path = os.path.join(ROOT, 'testing',
                                       'refreshinghgwebdir.py')

        env = os.environ.copy()
        env['HGRCPATH'] = global_hgrc
        env['HGENCODING'] = 'UTF-8'
        args = [
            self._hg,
            '--config', 'extensions.refreshinghgwebdir=%s' % refreshing_path,
            'serve',
            '-d',
            '-p', str(port),
            '--pid-file', self._hg_pid_path,
            '--web-conf', web_conf,
            '--accesslog', os.path.join(self._path, 'hg.access.log'),
            '--errorlog', os.path.join(self._path, 'hg.error.log'),
        ]
        # We execute from / so Mercurial doesn't pick up config files
        # from parent directories.
        subprocess.check_call(args, env=env, cwd='/')

        with open(self._hg_pid_path, 'rb') as fh:
            pid = fh.read().strip()

        return pid


class LocalMercurialRepository(object):
    """An interface to a Mercurial repository on the local filesystem.

    This class facilitates easily running ``hg`` commands against a local
    repository from the context of Python.
    """
    def __init__(self, hg, path, default_url, push_url=None, ircnick=None,
                 bugzilla_username=None, bugzilla_password=None):
        """Create a local Mercurial repository.

        ``hg`` is the hg binary to use.
        ``path`` is the local path to initialize the repository at.
        ``default_url`` is the URL for the default path to the repository.
        ``push_url`` is the default URL to be used for pushing.
        ``ircnick`` is the IRC nickname to use.
        ``bugzilla_username`` and ``bugzilla_password`` define the credentials
        to use when talking to Bugzilla or MozReview.
        """
        self.hg = hg
        self.path = path

        if not os.path.exists(path):
            subprocess.check_call([self.hg, 'init', path], cwd='/')

        dummyssh = os.path.join(ROOT, 'pylib', 'mercurial-support', 'dummyssh')
        reviewboard = os.path.join(ROOT, 'hgext', 'reviewboard', 'client.py')

        with open(os.path.join(path, '.hg', 'hgrc'), 'w') as fh:
            fh.write('\n'.join([
                '[paths]',
                'default = %s' % default_url,
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
                'ssh = python "%s"' % dummyssh,
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

        return subprocess.check_output(cmd, cwd=self.path,
                                       stderr=subprocess.STDOUT,
                                       env=env)

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
