# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import signal
import subprocess
import sys
import time
import urllib

from contextlib import contextmanager

import psutil

SETTINGS_LOCAL = """
from __future__ import unicode_literals

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'reviewboard.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}

LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))
PRODUCTION = False

SECRET_KEY = "mbr7-l=uhl)rnu_dgl)um$62ad2ay=xw+$oxzo_ct!$xefe780"
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
LDAP_TLS = False
LOGGING_ENABLED = True
LOGGING_LEVEL = "DEBUG"
LOGGING_DIRECTORY = "."
LOGGING_ALLOW_PROFILING = True
DEBUG = True
INTERNAL_IPS = "127.0.0.1"

""".strip()

@contextmanager
def wrap_env():
    old_env = os.environ.copy()
    old_cwd = os.getcwd()
    old_path = sys.path

    try:
        yield
    finally:
        sys.path = old_path
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)


class MozReviewBoard(object):
    """Interact with a Mozilla-flavored Review Board install."""

    def __init__(self, path, bugzilla_url=None,
            pulse_host=None, pulse_port=None,
            pulse_user='guest', pulse_password='guest'):
        self.path = os.path.abspath(path)
        self.manage = [sys.executable, '-m', 'reviewboard.manage']
        self.bugzilla_url = bugzilla_url
        self.pulse_host = pulse_host
        self.pulse_port = pulse_port
        self.pulse_user = pulse_user
        self.pulse_password = pulse_password

    def create(self):
        """Install Review Board."""
        with wrap_env():
            self._setup_env()
            self._create()

    def add_repository(self, name, url):
        """Add a repository to Review Board."""
        with wrap_env():
            self._setup_env()

            from reviewboard.scmtools.models import Repository, Tool
            tool = Tool.objects.get(name__exact='Mercurial')
            r = Repository(name=name, path=url, tool=tool)
            r.save()
            return r.id

    def start(self, port):
        """Start the HTTP server on the specified port."""
        with wrap_env():
            self._setup_env()
            self._start(port)

    def stop(self):
        path = os.path.join(self.path, 'rbserver.pid')
        if not os.path.exists(path):
            return

        with open(path, 'rb') as fh:
            pid = int(fh.read())

        os.kill(pid, signal.SIGINT)

        while psutil.pid_exists(pid):
            time.sleep(0.1)

        os.unlink(path)

    def _setup_env(self):
        sys.path.insert(0, self.path)
        env = os.environ.copy()
        env['PYTHONPATH'] = '%s:%s' % (self.path, env.get('PYTHONPATH', ''))
        os.environ['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'

        if not os.path.exists(self.path):
            os.mkdir(self.path)
        os.chdir(self.path)

        # Some Django operations put things in TMP. This mucks with concurrent
        # execution. So, we pin TMP to the instance.
        tmpdir = os.path.join(self.path, 'tmp')
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)

        env['TMPDIR'] = tmpdir
        self.env = env

    def _create(self):
        with open(os.path.join(self.path, 'settings_local.py'), 'wb') as fh:
            fh.write(SETTINGS_LOCAL)

        # TODO figure out how to suppress logging when invoking via native
        # Python API.
        f = open(os.devnull, 'w')
        subprocess.check_call(self.manage + ['syncdb', '--noinput'],
                cwd=self.path, env=self.env, stdout=f, stderr=f)

        subprocess.check_call(self.manage + ['enable-extension',
            'mozreview.extension.MozReviewExtension'],
            cwd=self.path, env=self.env, stdout=f, stderr=f)

        subprocess.check_call(self.manage + ['enable-extension',
            'rbbz.extension.BugzillaExtension'], cwd=self.path,
            env=self.env, stdout=f, stderr=f)

        subprocess.check_call(self.manage + ['enable-extension',
            'rbmozui.extension.RBMozUI'],
            cwd=self.path, env=self.env, stdout=f, stderr=f)

        from reviewboard.cmdline.rbsite import Site, parse_options
        class dummyoptions(object):
            no_input = True
            site_root = '/'
            db_type = 'sqlite3'
            copy_media = True

        site = Site(self.path, dummyoptions())
        site.rebuild_site_directory()

        from djblets.siteconfig.models import SiteConfiguration
        sc = SiteConfiguration.objects.get_current()
        sc.set('site_static_root', os.path.join(self.path, 'htdocs', 'static'))
        sc.set('site_media_root', os.path.join(self.path, 'htdocs', 'media'))

        # Hook up rbbz authentication.
        sc.set('auth_backend', 'bugzilla')
        sc.set('auth_bz_xmlrpc_url', '%s/xmlrpc.cgi' % self.bugzilla_url)
        sc.save()

        # Hook up Pulse.
        from djblets.extensions.models import RegisteredExtension
        mre = RegisteredExtension.objects.get(class_name='mozreview.extension.MozReviewExtension')
        mre.settings['pulse_host'] = self.pulse_host
        mre.settings['pulse_port'] = self.pulse_port
        mre.settings['pulse_user'] = self.pulse_user
        mre.settings['pulse_password'] = self.pulse_password
        mre.settings['pulse_ssl'] = False
        mre.save()

    def _start(self, port):
        port = str(port)
        env = self.env
        env['HOME'] = self.path
        f = open(os.path.join(self.path, 'reviewboard-server.log'), 'w')
        # --noreload prevents process for forking. If we don't do this,
        # our written pid is not correct.
        proc = subprocess.Popen(self.manage + ['runserver', '--noreload', port],
            cwd=self.path, env=env, stderr=f, stdout=f)

        # We write the PID to DAEMON_PIDS so Mercurial kills it automatically
        # if it is running.
        if 'DAEMON_PIDS' in env:
            with open(env['DAEMON_PIDS'], 'ab') as fh:
                fh.write('%d\n' % proc.pid)

        # We write the PID to a local file so the test can kill it. The benefit
        # of having the test kill it (with SIGINT as opposed to SIGKILL) is
        # that coverage information will be written if the process is stopped
        # with SIGINT.
        # TODO consider changing Mercurial to SIGINT first, SIGKILL later.
        with open(os.path.join(self.path, 'rbserver.pid'), 'wb') as fh:
            fh.write('%d' % proc.pid)

        # There is a race condition between us exiting and the tests
        # querying the server before it is ready. So, we wait on the
        # server before proceeding.
        while True:
            try:
                urllib.urlopen('http://localhost:%s/' % port)
                break
            except IOError:
                time.sleep(0.1)

        # We need to go through the double fork and session leader foo
        # to get this process to detach from the shell the process runs
        # under otherwise this process will keep it alive and the Mercurial
        # test runner will think the test is still running. Oy.
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        os.chdir('/')
        os.setsid()
        os.umask(0)

        pid = os.fork()
        if pid > 0:
            return pid

        sys.stdout.flush()
        sys.stderr.flush()

        os.dup2(f.fileno(), sys.stdin.fileno())
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())

        # And we spin forever.
        try:
            proc.wait()
        except Exception as e:
            print(e)
            sys.exit(1)

        sys.exit(0)
