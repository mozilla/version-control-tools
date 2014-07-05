#!/usr/bin/env python

# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file is used to run all Mercurial-related tests in this repository.

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


def find_test_files():
    """Find all test files in this repository."""
    for d in os.listdir(EXTDIR):
        if d.startswith('.'):
            continue

        test_dir = os.path.join(EXTDIR, d, 'tests')
        if not os.path.isdir(test_dir):
            continue

        for f in os.listdir(test_dir):
            if f.startswith('.'):
                continue

            if f.startswith('test-') and f.endswith(('.py', '.t')):
                yield os.path.join(test_dir, f)


if __name__ == '__main__':
    if not hasattr(sys, 'real_prefix'):
        raise Exception('You are not running inside the virtualenv. Please '
                'run `create-test-environment` and `source venv/bin/activate`')

    hg = os.path.join(os.path.dirname(sys.executable), 'hg')
    sys.argv.extend(['--with-hg', hg])

    coveragerc = os.path.join(HERE, '.coveragerc')
    coverdir = os.path.join(HERE, 'coverage')
    if not os.path.exists(coverdir):
        os.mkdir(coverdir)

    docoverage = '--cover' in sys.argv
    sys.argv = [a for a in sys.argv if a != '--cover']

    # run-tests.py's coverage options don't work for us... yet. So, we hack
    # in code coverage manually.
    if docoverage:
        os.environ['COVERAGE_DIR'] = coverdir
        os.environ['CODE_COVERAGE'] = '1'

    from vagrant import Vagrant
    vm = Vagrant(os.path.join(HERE, 'testing', 'bmoserver'), quiet_stdout=False)
    oldvmstate = vm.status()[0].state
    if oldvmstate != vm.RUNNING:
        vm.up()
        print('Brought up BMO virtual machine.')
    os.environ['BUGZILLA_URL'] = 'http://localhost:12000'

    runner = runtestsmod.TestRunner()
    sys.argv.extend(find_test_files())

    res = runner.run(sys.argv[1:])

    if oldvmstate in (vm.NOT_CREATED, vm.POWEROFF, vm.ABORTED):
        vm.halt()
    elif oldvmstate == vm.SAVED:
        vm.suspend()

    from coverage import coverage

    if docoverage:
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
