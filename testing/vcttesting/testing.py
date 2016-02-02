# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import errno
import os
import re
import subprocess
import sys
import time

from coverage import coverage


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


PYTHON_COVERAGE_DIRS = (
    'hgext',
    'pylib',
    'hghooks',
)

# Directories containing Python unit tests.
UNIT_TEST_DIRS = [
    'autoland/tests',
    'git/tests',
    'hgserver/tests',
    'pylib',
]

# Directories whose Python unit tests we should ignore.
UNIT_TEST_IGNORES = (
    'pylib/Bugsy',
    'pylib/flake8',
    'pylib/mccabe',
    'pylib/pep8',
    'pylib/pyflakes',
    'pylib/requests',
)

COVERAGE_OMIT = (
    'venv/*',
    'pylib/Bugsy/*',
    'pylib/flake/*',
    'pylib/mccabe/*',
    'pylib/mercurial-support/*',
    'pylib/pep8/*',
    'pylib/pyflakes/*',
    'pylib/requests/*',
)


def is_test_filename(f):
    """Is a path a test file."""
    return f.startswith('test-') and f.endswith(('.py', '.t'))


def get_extensions(extdir):
    """Obtain information about extensions.

    Returns a dict mapping extension name to metadata.
    """
    m = {}

    for d in os.listdir(extdir):
        ext_dir = os.path.join(extdir, d)

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

    hooks_test_dir = os.path.join(ROOT, 'hghooks', 'tests')
    hook_tests = [os.path.join(hooks_test_dir, f)
                   for f in os.listdir(hooks_test_dir)
                   if is_test_filename(f)]

    unit_tests = []
    for base in UNIT_TEST_DIRS:
        base = os.path.join(ROOT, base)
        for root, dirs, files in os.walk(base):
            relative = root[len(ROOT) + 1:]
            if relative.startswith(UNIT_TEST_IGNORES):
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


def docker_requirements(tests):
    """Whether any of the specified test files require Docker."""
    docker_keywords = (
        b'MozReviewTest',
        b'MozReviewWebDriverTest',
    )

    hgmo = False
    mozreview = False
    bmo = False
    d = False

    for t in tests:
        with open(t, 'rb') as fh:
            content = fh.read()

            if b'#require hgmodocker' in content:
                d = True
                hgmo = True

            if b'#require mozreviewdocker' in content:
                d = True
                mozreview = True
                bmo = True

            if b'#require bmodocker' in content:
                d = True
                bmo = True

            if b'#require docker' in content:
                raise Exception('"#require docker" is not longer supported: '
                                'use "#require {hgmo,mozreview,bmo}docker"')

            for keyword in docker_keywords:
                if keyword in content:
                    # This could probably be defined better.
                    d = True
                    hgmo = True
                    mozreview = True

    return d, hgmo, mozreview, bmo


def get_docker_state(docker, tests, verbose=False, use_last=False):
    build_docker, hgmo, mozreview, bmo = docker_requirements(tests)

    if not build_docker:
        return {}

    env = {}
    print('generating Docker images needed for tests')
    t_start = time.time()
    mr_images, hgmo_images, bmo_images = docker.build_all_images(
            verbose=verbose,
            use_last=use_last,
            hgmo=hgmo,
            mozreview=mozreview,
            bmo=bmo)

    t_end = time.time()
    print('got Docker images in %.2fs' % (t_end - t_start))
    if mozreview:
        env['DOCKER_PULSE_IMAGE'] = mr_images['pulse']
        env['DOCKER_HGRB_IMAGE'] = mr_images['hgrb']
        env['DOCKER_AUTOLANDDB_IMAGE'] = mr_images['autolanddb']
        env['DOCKER_AUTOLAND_IMAGE'] = mr_images['autoland']
        env['DOCKER_RBWEB_IMAGE'] = mr_images['rbweb']
        env['DOCKER_TREESTATUS_IMAGE'] = mr_images['treestatus']
        env['DOCKER_LDAP_IMAGE'] = mr_images['ldap']
        if not hgmo:
            env['DOCKER_HGWEB_IMAGE'] = mr_images['hgweb']
        if not bmo:
            env['DOCKER_BMO_DB_IMAGE'] = mr_images['bmodb']
            env['DOCKER_BMO_WEB_IMAGE'] = mr_images['bmoweb']

    if hgmo:
        env['DOCKER_HGMASTER_IMAGE'] = hgmo_images['hgmaster']
        env['DOCKER_HGWEB_IMAGE'] = hgmo_images['hgweb']
        env['DOCKER_LDAP_IMAGE'] = hgmo_images['ldap']

    if bmo:
        env['DOCKER_BMO_DB_IMAGE'] = bmo_images['bmodb']
        env['DOCKER_BMO_WEB_IMAGE'] = bmo_images['bmoweb']

    return env


def produce_coverage_reports(coverdir):
    cov = coverage(data_file=os.path.join(coverdir, 'coverage'))
    cov.combine()

    pydirs = [os.path.join(ROOT, d) for d in PYTHON_COVERAGE_DIRS]
    omit = [os.path.join(ROOT, d) for d in COVERAGE_OMIT]

    # Ensure all .py files show up in coverage report.
    for d in pydirs:
        for root, dirs, files in os.walk(d):
            for f in files:
                if f.endswith('.py'):
                    cov.data.touch_file(os.path.join(root, f))

    cov.html_report(directory=os.path.join(coverdir, 'html'),
                    ignore_errors=True, omit=omit)
    cov.xml_report(outfile=os.path.join(coverdir, 'coverage.xml'),
                   ignore_errors=True, omit=omit)


def run_nose_tests(tests, process_count=None, verbose=False):
    """Run nose tests and return result code."""
    noseargs = [sys.executable, '-m', 'nose.core', '-s']

    if process_count and process_count > 1:
        noseargs.extend([
            '--processes=%d' % process_count,
            '--process-timeout=120',
        ])

    if verbose:
        noseargs.append('-v')
    else:
        noseargs.append('--nologcapture')

    noseargs.extend(tests)

    env = dict(os.environ)
    paths = [p for p in env.get('PYTHONPATH', '').split(os.pathsep) if p]

    # We need the directory with sitecustomize.py in sys.path for code
    # coverage to work. This is arguably a bug in the location of
    # sitecustomize.py.
    paths.append(os.path.dirname(sys.executable))

    return subprocess.call(noseargs, env=env)


def get_hg_version(hg):
    env = dict(os.environ)
    env[b'HGPLAIN'] = b'1'
    env[b'HGRCPATH'] = b'/dev/null'
    out = subprocess.check_output('%s --version' % hg,
                                  env=env, shell=True)
    out = out.splitlines()[0]
    match = re.search('version ([^\+\)]+)', out)
    if not match:
        return None

    return match.group(1)


def remove_err_files(tests):
    for t in tests:
        err = '%s.err' % t
        try:
            os.remove(err)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
