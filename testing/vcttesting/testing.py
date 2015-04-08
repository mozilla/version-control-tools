# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os

import concurrent.futures as futures


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


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

    # Directories containing Python unit tests.
    unit_test_dirs = [
        'autoland/tests',
        'scripts/pash/tests',
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
        base = os.path.join(ROOT, base)
        for root, dirs, files in os.walk(base):
            relative = root[len(ROOT) + 1:]
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


def prune_docker_orphans(docker, containers, images):
    """Prune Docker containers and images that were orphaned from tests.

    If tests are aborted, Docker containers and images could linger. This will
    clean them.
    """
    if not docker.is_alive():
        return

    with futures.ThreadPoolExecutor(4) as e:
        for c in docker.client.containers(all=True):
            if c['Id'] not in containers:
                print('removing orphaned docker container: %s' %
                      c['Id'])
                e.submit(docker.client.remove_container, c['Id'],
                         force=True)

    with futures.ThreadPoolExecutor(4) as e:
        for i in docker.client.images(all=True):
            if i['Id'] not in images:
                print('removing orphaned docker image: %s' % c['Id'])
                e.submit(docker.client.remove_image, c['Id'])
