# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import signal
import subprocess
import sys
import time
import urllib

import psutil
import yaml

from mach.main import Mach

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.join(HERE, '..', '..', '..')
sys.path.insert(0, os.path.normpath(os.path.join(ROOT, 'testing')))

def main(args):
    m = Mach(os.getcwd())

    m.define_category('reviewboard', 'Review Board',
        'Interface with Review Board', 50)
    import vcttesting.reviewboard.mach_commands

    legacy_actions = set([
        'start',
        'stop',
        'reopen',
        'dump-user',
    ])

    use_mach = True

    try:
        path, action = args[0:2]
        if action in legacy_actions:
            use_mach = False
    except Exception:
        pass

    if use_mach:
        return m.run(args)

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

    if action == 'start':
        port = args[2]

        env['HOME'] = path
        f = open(os.devnull, 'w')
        # --noreload prevents process for forking. If we don't do this,
        # our written pid is not correct.
        proc = subprocess.Popen(manage + ['runserver', '--noreload', port],
            cwd=path, env=env, stderr=f, stdout=f)

        # We write the PID to DAEMON_PIDS so Mercurial kills it automatically
        # if it is running.
        with open(env['DAEMON_PIDS'], 'ab') as fh:
            fh.write('%d\n' % proc.pid)

        # We write the PID to a local file so the test can kill it. The benefit
        # of having the test kill it (with SIGINT as opposed to SIGKILL) is
        # that coverage information will be written if the process is stopped
        # with SIGINT.
        # TODO consider changing Mercurial to SIGINT first, SIGKILL later.
        with open(os.path.join(path, 'rbserver.pid'), 'wb') as fh:
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

    # You should call this so the server stop gracefully and records code
    # coverage data. Otherwise, Mercurial will kill it with SIGKILL and no
    # coverage data will be saved.
    elif action == 'stop':
        with open(os.path.join(path, 'rbserver.pid'), 'rb') as fh:
            pid = int(fh.read())

        os.kill(pid, signal.SIGINT)

        while psutil.pid_exists(pid):
            time.sleep(0.1)

    elif action == 'reopen':
        port, rid = args[2:]
        root = get_root(port)
        r = root.get_review_request(review_request_id=rid)
        response = r.update(status='pending')

    elif action == 'dump-user':
        port, username = args[2:]
        root = get_root(port)
        u = root.get_user(username=username)

        o = {}
        for field in u.iterfields():
            o[field] = getattr(u, field)

        data = {}
        data[u.id] = o

        print(yaml.safe_dump(data, default_flow_style=False).rstrip())


def get_root(port):
    from rbtools.api.client import RBClient

    username = os.environ.get('BUGZILLA_USERNAME')
    password = os.environ.get('BUGZILLA_PASSWORD')

    c = RBClient('http://localhost:%s/' % port, username=username,
            password=password)
    return c.get_root()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
