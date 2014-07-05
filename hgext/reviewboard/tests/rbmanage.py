# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys
import time
import urllib

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


def main(args):
    path, action = args[0:2]
    path = os.path.abspath(path)
    sys.path.insert(0, path)

    env = os.environ.copy()
    env['PYTHONPATH'] = '%s:%s' % (path, env.get('PYTHONPATH', ''))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'
    manage = [sys.executable, '-m', 'reviewboard.manage']

    if not os.path.exists(path):
        os.mkdir(path)
    os.chdir(path)

    # Some Django operations put things in TMP. This messages with
    # concurrent test execution.
    tmpdir = os.path.join(path, 'tmp')
    if not os.path.exists(tmpdir):
        os.mkdir(tmpdir)
    env['TMPDIR'] = tmpdir

    if action == 'create':
        with open(os.path.join(path, 'settings_local.py'), 'wb') as fh:
            fh.write(SETTINGS_LOCAL)

        # TODO figure out how to suppress logging when invoking via native
        # Python API.
        f = open(os.devnull, 'w')
        subprocess.check_call(manage + ['syncdb', '--noinput'], cwd=path,
                env=env, stdout=f, stderr=f)

        subprocess.check_call(manage + ['enable-extension',
            'rbbz.extension.BugzillaExtension'], cwd=path,
            env=env, stdout=f, stderr=f)

        subprocess.check_call(manage + ['enable-extension',
            'rbmozui.extension.RBMozUI'],
            cwd=path, env=env, stdout=f, stderr=f)

        # As long as we create a user here, rbbz will still authenticate it.
        # Ideally, we'd create a user in Bugzilla and only have users
        # go through rbbz/Bugzilla.
        subprocess.check_call(manage + ['createsuperuser', '--username',
            'testadmin', '--email', 'testadmin@example.com', '--noinput'], cwd=path,
            env=env, stderr=f, stdout=f)

        from django.contrib.auth.models import User
        u = User.objects.get(username__exact='testadmin')
        u.set_password('password')
        u.save()

        from reviewboard.cmdline.rbsite import Site, parse_options
        class dummyoptions(object):
            no_input = True
            site_root = '/'
            db_type = 'sqlite3'
            copy_media = True

        site = Site(path, dummyoptions())
        site.rebuild_site_directory()

        from djblets.siteconfig.models import SiteConfiguration
        sc = SiteConfiguration.objects.get_current()
        sc.set('site_static_root', os.path.join(path, 'htdocs', 'static'))
        sc.set('site_media_root', os.path.join(path, 'htdocs', 'media'))

        # Hook up rbbz authentication.
        sc.set('auth_backend', 'bugzilla')
        sc.set('auth_bz_xmlrpc_url', '%s/xmlrpc.cgi' % os.environ['BUGZILLA_URL'])

        sc.save()

    elif action == 'repo':
        name, url = args[2:]

        from reviewboard.scmtools.models import Repository, Tool
        tool = Tool.objects.get(name__exact='Mercurial')
        r = Repository(name=name, path=url, tool=tool)
        r.save()
    elif action == 'start':
        port = args[2]

        env['HOME'] = path
        f = open(os.devnull, 'w')
        # --noreload prevents process for forking. If we don't do this,
        # our written pid is not correct.
        proc = subprocess.Popen(manage + ['runserver', '--noreload', port],
            cwd=path, env=env, stderr=f, stdout=f)

        with open(env['DAEMON_PIDS'], 'ab') as fh:
            fh.write('%d\n' % proc.pid)

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
            sys.exit(0)

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

    elif action == 'dumpreview':
        port, rid = args[2:]

        from rbtools.api.client import RBClient
        c = RBClient('http://localhost:%s/' % port, username='testadmin',
                password='password')
        root = c.get_root()

        r = root.get_review_request(review_request_id=rid)

        # TODO Figure out depends_on dumping.
        print('Review: %s' % r.id)
        print('  Status: %s' % r.status)
        if r.bugs_closed:
            print('  Bugs: %s' % ' '.join(r.bugs_closed))
        print('  Commit ID: %s' % r.commit_id)
        if r.summary:
            print('  Summary: %s' % r.summary)
        if r.description:
            print('  Description:\n    %s' % r.description.replace('\n', '\n    '))
        print('  Extra:')
        for k, v in sorted(r.extra_data.iteritems()):
            print ('    %s: %s' % (k, v))


        d = r.get_or_create_draft()
        print('Draft: %s' % d.id)
        if d.bugs_closed:
            print('  Bugs: %s' % ' '.join(d.bugs_closed))
        print('  Commit ID: %s' % d.commit_id)
        if d.summary:
            print('  Summary: %s' % d.summary)
        if d.description:
            print('  Description:\n    %s' % d.description.replace('\n', '\n    '))
        print('  Extra:')
        for k, v in sorted(d.extra_data.iteritems()):
            print('    %s: %s' % (k, v))

        dds = d.get_draft_diffs()
        for diff in dds:
            print('Diff: %s' % diff.id)
            print('  Revision: %s' % diff.revision)
            if diff.base_commit_id:
                print('  Base Commit: %s' % diff.base_commit_id)
            patch = diff.get_patch()
            print(patch.data)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
