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
                'create one and `pip install -r test-requirements.txt`')

    hg = os.path.join(os.path.dirname(sys.executable), 'hg')
    sys.argv.extend(['--with-hg', hg])

    runner = runtestsmod.TestRunner()
    sys.argv.extend(find_test_files())
    sys.exit(runner.run(sys.argv[1:]))
