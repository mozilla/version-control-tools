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

                if f.startswith('test-') and f.endswith(('.py', '.t')):
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

    # --all-versions belongs to use only. Don't pass it along
    sys.argv = [a for a in sys.argv if a != '--all-versions']

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

    extensions = get_extensions()

    # Add all tests unless we get an argument that looks like a test path.
    if not any(a for a in extra[1:] if not a.startswith('-')):
        for e in extensions.values():
            sys.argv.extend(sorted(e['tests']))

    old_env = os.environ.copy()
    old_defaults = dict(runtestsmod.defaults)
    res = runner.run(sys.argv[1:])
    os.environ.clear()
    os.environ.update(old_env)
    runtestsmod.defaults = dict(old_defaults)

    # If we're running the full compatibility run, figure out what versions
    # apply to what and run them.
    if options.all_versions:
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

            print('Testing with Mercurial %s' % version)
            runner = runtestsmod.TestRunner()
            res2 = runner.run(sys.argv[1:])
            if res2:
                res = res2
            os.environ.clear()
            os.environ.update(old_env)
            runtestsmod.defaults = dict(old_defaults)

    #if oldvmstate in (vm.NOT_CREATED, vm.POWEROFF, vm.ABORTED):
    #    vm.halt()
    #elif oldvmstate == vm.SAVED:
    #    vm.suspend()

    from coverage import coverage

    if options.cover:
        cov = coverage(data_file=os.path.join(coverdir, 'coverage'))
        cov.combine()
        cov.html_report(directory='coverage/html', ignore_errors=True,
            omit=[
                os.path.join(HERE, 'venv', '*'),
                os.path.join(HERE, 'pylib', 'flake8', '*'),
                os.path.join(HERE, 'pylib', 'mccabe', '*'),
                os.path.join(HERE, 'pylib', 'mercurial-support', '*'),
                os.path.join(HERE, 'pylib', 'pep8', '*'),
                os.path.join(HERE, 'pylib', 'pyflakes', '*'),
            ])

    sys.exit(res)
