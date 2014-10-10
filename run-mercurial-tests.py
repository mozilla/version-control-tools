#!/usr/bin/env python

# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This file is used to run all Mercurial-related tests in this repository.

from __future__ import print_function

import argparse
import imp
import os
import re
import subprocess
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

def get_test_files(extensions):
    extension_tests = []
    for e in extensions.values():
        extension_tests.extend(e['tests'])

    hooks_test_dir = os.path.join(HERE, 'hghooks', 'tests')
    hook_tests = [os.path.join(hooks_test_dir, f)
                   for f in os.listdir(hooks_test_dir)
                   if is_test_filename(f)]

    # Directories containing Python unit tests.
    unit_test_dirs = [
        'pylib',
    ]

    # Directories whose Python unit tests we should ignore.
    unit_test_ignores = (
        'pylib/Bugsy',
        'pylib/flake8',
        'pylib/mccabe',
        'pylib/pep8',
        'pylib/pyflakes',
        'pylib/requests',
    )

    unit_tests = []
    for base in unit_test_dirs:
        base = os.path.join(HERE, base)
        for root, dirs, files in os.walk(base):
            relative = root[len(HERE) + 1:]
            if relative.startswith(unit_test_ignores):
                continue

            for f in files:
                if f.startswith('test') and f.endswith('.py'):
                    unit_tests.append(os.path.join(root, f))
                elif f.startswith('test') and f.endswith('.t'):
                    # These aren't technically hooks. But it satifies the
                    # requirement of putting .t tests elsewhere easily.
                    hook_tests.append(os.path.join(root, f))

    return {
        'extension': sorted(extension_tests),
        'hook': sorted(hook_tests),
        'unit': sorted(unit_tests),
        'all': set(extension_tests) | set(hook_tests) | set(unit_tests),
    }


if __name__ == '__main__':
    if not hasattr(sys, 'real_prefix'):
        raise Exception('You are not running inside the virtualenv. Please '
                'run `create-test-environment` and `source venv/bin/activate`')

    from vcttesting.docker import Docker

    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    parser = argparse.ArgumentParser()
    parser.add_argument('--with-hg')
    parser.add_argument('-C', '--cover', action='store_true')
    parser.add_argument('-j', '--jobs', type=int)
    parser.add_argument('--all-versions', action='store_true',
        help='Test against all marked compatible versions')
    parser.add_argument('--no-hg-tip', action='store_true',
        help='Do not run tests against the @ bookmark of hg')
    parser.add_argument('--no-unit', action='store_true',
        help='Do not run Python unit tests')

    options, extra = parser.parse_known_args(sys.argv)

    if not options.jobs:
        print('WARNING: Not running tests optimally. Specify -j to run tests '
                'in parallel.', file=sys.stderr)

    # some arguments belong to us only. Don't pass it along to run-tests.py.
    sys.argv = [a for a in sys.argv
        if a not in set(['--all-versions', '--no-hg-tip'])]

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
    verbose = '-v' in sys.argv or '--verbose' in sys.argv

    # We take a snapshot of Docker containers and images before we start tests
    # so we can look for leaks later.
    #
    # This behavior is non-ideal: we should not leak Docker containers and
    # images. Furthermore, if others interact with Docker while we run, bad
    # things will happen. But this is the easiest solution, so hacks win.
    preserve_containers = set()
    preserve_images = set()

    # Enable tests to interact with our Docker controlling script.
    docker_state = os.path.join(HERE, '.docker-state.json')
    docker = Docker(docker_state, os.environ.get('DOCKER_HOST', None))
    if docker.is_alive():
        os.environ['DOCKER_HOSTNAME'] = docker.docker_hostname

        # We build the base BMO images in the test runner because doing it
        # from tests would be racey. It is easier to do it here instead of
        # complicating code with locks.
        db_image, web_image = docker.build_bmo(verbose=verbose,
                allow_dirty=True)
        os.environ['DOCKER_BMO_DB_IMAGE'] = db_image
        os.environ['DOCKER_BMO_WEB_IMAGE'] = web_image

        for c in docker.client.containers(all=True):
            preserve_containers.add(c['Id'])
        for i in docker.client.images(all=True):
            preserve_images.add(i['Id'])

    os.environ['BUGZILLA_USERNAME'] = 'admin@example.com'
    os.environ['BUGZILLA_PASSWORD'] = 'password'

    runner = runtestsmod.TestRunner()

    orig_args = list(sys.argv)

    if not options.with_hg:
        hg = os.path.join(os.path.dirname(sys.executable), 'hg')
        sys.argv.extend(['--with-hg', hg])

    sys.argv.extend(['--xunit',
        os.path.join(HERE, 'coverage', 'results.xml')])

    extensions = get_extensions()

    test_files = get_test_files(extensions)
    extension_tests = test_files['extension']
    unit_tests = test_files['unit']
    hook_tests = test_files['hook']

    possible_tests = [os.path.normpath(os.path.abspath(a))
                      for a in extra[1:] if not a.startswith('-')]
    requested_tests = [a for a in possible_tests if a in test_files['all']]

    # Add all Mercurial tests unless we get an argument that is a known test.
    if not requested_tests:
        sys.argv.extend(extension_tests)
        sys.argv.extend(hook_tests)

    old_env = os.environ.copy()
    old_defaults = dict(runtestsmod.defaults)

    # This is used by hghave to detect the running Mercurial because run-tests
    # doesn't pass down the version info in the environment of the hghave
    # invocation.
    import mercurial.__version__
    hgversion = mercurial.__version__.version
    os.environ['HGVERSION'] = hgversion

    if options.with_hg:
        clean_env = dict(os.environ)
        clean_env['HGPLAIN'] = '1'
        clean_env['HGRCPATH'] = '/dev/null'
        out = subprocess.check_output('%s --version' % options.with_hg,
                env=clean_env, shell=True)
        out = out.splitlines()[0]
        match = re.search('version ([^\+\)]+)', out)
        if not match:
            print('ERROR: Unable to identify Mercurial version.')
            sys.exit(1)

        hgversion = match.group(1)
        os.environ['HGVERSION'] = hgversion

    res = runner.run(sys.argv[1:])
    os.environ.clear()
    os.environ.update(old_env)
    runtestsmod.defaults = dict(old_defaults)

    run_unit_tests = unit_tests
    if requested_tests:
        run_unit_tests = [t for t in requested_tests if t in unit_tests]
    if options.no_unit:
        run_unit_tests = []

    if run_unit_tests:
        noseargs = [sys.executable, '-m', 'nose.core', '-s']
        noseargs.extend(unit_tests)

        env = dict(os.environ)
        paths = [p for p in env.get('PYTHONPATH', '').split(os.pathsep) if p]

        # We need the directory with sitecustomize.py in sys.path for code
        # coverage to work. This is arguably a bug in the location of
        # sitecustomize.py.
        paths.append(os.path.dirname(sys.executable))

        for p in os.listdir(os.path.join(HERE, 'pylib')):
            p = os.path.join(HERE, 'pylib', p)
            if os.path.isdir(p) and p not in paths:
                paths.insert(0, p)

        env['PYTHONPATH'] = ':'.join(paths)

        noseres = subprocess.call(noseargs, env=env)
        if noseres:
            res = noseres

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

        mercurials_dir = os.path.normpath(os.path.abspath(os.path.join(
            os.environ['VIRTUAL_ENV'], 'mercurials')))

        # Maps directories/versions to lists of tests to run.
        # We normalize X.Y.Z to X.Y for compatibility because the monthly
        # minor releases of Mercurial shouldn't change behavior. If an
        # extension is marked as compatible with X.Y, we run its tests
        # against all X.Y and X.Y.Z releases seen on disk.
        versions = {}
        for dirver in os.listdir(mercurials_dir):
            if dirver.startswith('.') or dirver == '@':
                continue

            normdirver = '.'.join(dirver.split('.')[0:2])

            tests = versions.setdefault(dirver, set())
            tests |= set(hook_tests)

            for e, m in sorted(extensions.items()):
                for extver in m['testedwith']:
                    normever = '.'.join(extver.split('.')[0:2])

                    if extver == dirver or normever == normdirver:
                        tests |= m['tests']

        def run_hg_tests(version, tests):
            if requested_tests:
                tests = [t for t in tests if t in requested_tests]

            if not tests:
                return

            sys.argv = list(orig_args)
            sys.argv.extend(['--with-hg',
                os.path.join(mercurials_dir, version, 'bin', 'hg')])
            sys.argv.extend(sorted(tests))

            print('Testing with Mercurial %s' % version)
            sys.stdout.flush()
            os.environ['HGVERSION'] = version
            runner = runtestsmod.TestRunner()
            r = runner.run(sys.argv[1:])
            os.environ.clear()
            os.environ.update(old_env)
            runtestsmod.defaults = dict(old_defaults)
            sys.stdout.flush()
            sys.stderr.flush()

        for version, tests in sorted(versions.items()):
            res2 = run_hg_tests(version, tests)
            if res2:
                res = res2

        # Run all tests against @ because we always want to be compatible
        # with the bleeding edge of development.
        if not options.no_hg_tip:
            all_hg_tests = []
            for e, m in extensions.items():
                all_hg_tests.extend(sorted(m['tests']))
            all_hg_tests.extend(hook_tests)
            run_hg_tests('@', all_hg_tests)


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

    # Clean up leaked Docker containers and images.
    if docker.is_alive():
        for c in docker.client.containers(all=True):
            if c['Id'] not in preserve_containers:
                print('Removing orphaned Docker container: %s' % c['Id'])
                docker.client.stop(c['Id'])
                docker.client.remove_container(c['Id'])

        for i in docker.client.images(all=True):
            if i['Id'] not in preserve_images:
                print('Removing orphaned Docker image: %s' % c['Id'])
                docker.client.remove_image(i['Id'])

    sys.exit(res)
