#!/usr/bin/env python

# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file is used to run all Mercurial-related tests in this repository.

from __future__ import print_function

import argparse
import imp
import os
import sys

# Mercurial's run-tests.py isn't meant to be loaded as a module. We do it
# anyway.
HERE = os.path.dirname(os.path.abspath(__file__))
RUNTESTS = os.path.join(HERE, 'pylib', 'mercurial-support', 'run-tests.py')
EXTDIR = os.path.join(HERE, 'hgext')

sys.path.insert(0, os.path.join(HERE, 'pylib', 'mercurial-support'))
runtestsmod = imp.load_source('runtests', RUNTESTS)

sys.path.insert(0, os.path.join(HERE, 'testing'))

def is_test_filename(f):
    return f.startswith('test-') and f.endswith(('.py', '.t'))

def get_extensions():
    """Obtain information about extensions.

    Returns a dict mapping extension name to metadata.
    """
    m = {}

    for d in os.listdir(EXTDIR):
        ext_dir = os.path.join(EXTDIR, d)

        if d.startswith('.') or not os.path.isdir(ext_dir):
            continue

        e = {'tests': set(), 'testedwith': set()}

        # Find test files.
        test_dir = os.path.join(ext_dir, 'tests')
        if os.path.isdir(test_dir):
            for f in os.listdir(test_dir):
                if f.startswith('.'):
                    continue

                if is_test_filename(f):
                    e['tests'].add(os.path.join(test_dir, f))

        # Look for compatibility info.
        for f in os.listdir(ext_dir):
            if f.startswith('.') or not f.endswith('.py'):
                continue

            with open(os.path.join(ext_dir, f), 'rb') as fh:
                lines = fh.readlines()

            for line in lines:
                if not line.startswith('testedwith'):
                    continue

                v, value = line.split('=', 1)
                value = value.strip().strip("'").strip('"').strip()
                e['testedwith'] = set(value.split())

        m[d] = e

    return m

if __name__ == '__main__':
    if not hasattr(sys, 'real_prefix'):
        raise Exception('You are not running inside the virtualenv. Please '
                'run `create-test-environment` and `source venv/bin/activate`')

    from vcttesting.docker import Docker

    parser = argparse.ArgumentParser()
    parser.add_argument('--with-hg')
    parser.add_argument('-C', '--cover', action='store_true')
    parser.add_argument('-j', '--jobs', type=int)
    parser.add_argument('--all-versions', action='store_true',
        help='Test against all marked compatible versions')

    options, extra = parser.parse_known_args(sys.argv)

    if not options.jobs:
        print('WARNING: Not running tests optimally. Specify -j to run tests '
                'in parallel.', file=sys.stderr)

    # some arguments belong to us only. Don't pass it along to run-tests.py.
    sys.argv = [a for a in sys.argv
        if a not in set(['--all-versions'])]

    coveragerc = os.path.join(HERE, '.coveragerc')
    coverdir = os.path.join(HERE, 'coverage')
    if not os.path.exists(coverdir):
        os.mkdir(coverdir)

    # run-tests.py's coverage options don't work for us... yet. So, we hack
    # in code coverage manually.
    if options.cover:
        os.environ['COVERAGE_DIR'] = coverdir
        os.environ['CODE_COVERAGE'] = '1'

    # We do our own code coverage. Strip it so run-tests.py doesn't try to do
    # it's own.
    sys.argv = [a for a in sys.argv if a != '--cover']

    # Enable tests to interact with our Docker controlling script.
    docker_state = os.path.join(HERE, '.docker-state.json')
    os.environ['DOCKER_STATE_FILE'] = docker_state
    docker = Docker(docker_state, os.environ.get('DOCKER_HOST', None))
    os.environ['DOCKER_HOSTNAME'] = docker.docker_hostname

    # TODO enable integration with virtual machine when it is ready.
    #from vagrant import Vagrant
    #vm = Vagrant(os.path.join(HERE, 'testing', 'bmoserver'), quiet_stdout=False)
    #oldvmstate = vm.status()[0].state
    #if oldvmstate != vm.RUNNING:
    #    vm.up()
    #    print('Brought up BMO virtual machine.')
    #os.environ['BUGZILLA_URL'] = 'http://localhost:12000'

    runner = runtestsmod.TestRunner()

    orig_args = list(sys.argv)

    if not options.with_hg:
        hg = os.path.join(os.path.dirname(sys.executable), 'hg')
        sys.argv.extend(['--with-hg', hg])

    sys.argv.extend(['--xunit',
        os.path.join(HERE, 'coverage', 'results.xml')])

    extensions = get_extensions()

    hooks_test_dir = os.path.join(HERE, 'hghooks', 'tests')
    hooks_tests = [os.path.join(hooks_test_dir, f)
                   for f in os.listdir(hooks_test_dir)
                   if is_test_filename(f)]

    # Add all tests unless we get an argument that looks like a test path.
    if not any(a for a in extra[1:] if not a.startswith('-')):
        for e in extensions.values():
            sys.argv.extend(sorted(e['tests']))
        sys.argv.extend(hooks_tests)

    old_env = os.environ.copy()
    old_defaults = dict(runtestsmod.defaults)
    res = runner.run(sys.argv[1:])
    os.environ.clear()
    os.environ.update(old_env)
    runtestsmod.defaults = dict(old_defaults)

    # If we're running the full compatibility run, figure out what versions
    # apply to what and run them.
    if options.all_versions:
        # No need to grab code coverage for legacy versions - it just slows
        # us down.
        # Assertion: we have no tests that only work on legacy Mercurial
        # versions.
        try:
            del os.environ['CODE_COVERAGE']
        except KeyError:
            pass

        versions = {}
        for e, m in extensions.items():
            for v in m['testedwith']:
                tests = versions.setdefault(v, set())
                tests |= m['tests']

        mercurials_dir = os.path.normpath(os.path.abspath(os.path.join(
            os.environ['VIRTUAL_ENV'], 'mercurials')))

        for version, tests in sorted(versions.items()):
            if not tests:
                continue

            sys.argv = list(orig_args)
            sys.argv.extend(['--with-hg',
                os.path.join(mercurials_dir, version, 'bin', 'hg')])
            sys.argv.extend(sorted(tests))
            sys.argv.extend(hooks_tests)

            print('Testing with Mercurial %s' % version)
            sys.stdout.flush()
            runner = runtestsmod.TestRunner()
            res2 = runner.run(sys.argv[1:])
            if res2:
                res = res2
            os.environ.clear()
            os.environ.update(old_env)
            runtestsmod.defaults = dict(old_defaults)
            sys.stdout.flush()
            sys.stderr.flush()

    #if oldvmstate in (vm.NOT_CREATED, vm.POWEROFF, vm.ABORTED):
    #    vm.halt()
    #elif oldvmstate == vm.SAVED:
    #    vm.suspend()

    from coverage import coverage

    if options.cover:
        cov = coverage(data_file=os.path.join(coverdir, 'coverage'))
        cov.combine()

        pydirs = [
            EXTDIR,
            os.path.join(HERE, 'pylib'),
            os.path.join(HERE, 'hghooks'),
        ]

        # Ensure all .py files show up in coverage report.
        for d in pydirs:
            for root, dirs, files in os.walk(d):
                for f in files:
                    if f.endswith('.py'):
                        cov.data.touch_file(os.path.join(root, f))

        omit = [
            os.path.join(HERE, 'venv', '*'),
            os.path.join(HERE, 'pylib', 'Bugsy', '*'),
            os.path.join(HERE, 'pylib', 'flake8', '*'),
            os.path.join(HERE, 'pylib', 'mccabe', '*'),
            os.path.join(HERE, 'pylib', 'mercurial-support', '*'),
            os.path.join(HERE, 'pylib', 'pep8', '*'),
            os.path.join(HERE, 'pylib', 'pyflakes', '*'),
            os.path.join(HERE, 'pylib', 'requests', '*'),
        ]

        cov.html_report(directory='coverage/html', ignore_errors=True,
                omit=omit)
        cov.xml_report(outfile='coverage/coverage.xml', ignore_errors=True,
                omit=omit)

    sys.exit(res)
