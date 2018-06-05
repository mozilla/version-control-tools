#!/usr/bin/env python
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# This script supplements ``hghave`` from Mercurial testing environment to
# support requirements specific to Mozilla. Some of the tests should
# arguably be added upstream. Until then, this file and the hacks around it
# exist.

# The way Mercurial's test runner processes ``#require`` directives is that
# it invokes an ``hghave`` script in the same directory as the test.
# This repository has numerous ``hghave`` scripts scattered about in
# directories containing tests that use ``#require``. Those scripts simply
# find this file and ``execfile()`` it (effectively doing a #include).
# Hacky, but it works.

import os
import sys
import tempfile

if 'REPO_ROOT' not in globals():
    print('hghave.py included wrong. please set REPO_ROOT variable in calling script')
    sys.exit(1)

# We import Mercurial's own ``hghave.py`` so we can declare our own checks.
HGHAVE_PY = os.path.join(REPO_ROOT, 'pylib', 'mercurial-support', 'hghave.py')
execfile(HGHAVE_PY)

# Need to supplement sys.path because PYTHONPATH isn't set properly
# from the context of run-tests.py. This is very hacky.
sys.path.insert(0, os.path.join(REPO_ROOT, 'testing'))

def have_docker_images(images):
    # These environment variables are exported by run-tests. If they aren't
    # present, we assume the Docker image isn't built and available.
    # If the environment variables aren't present, the test still works because
    # d0cker will build images automatically if needed. This slows down tests
    # drastically. So it is better to catch the issue sooner so the slowdown
    # can be identified.
    keys = [b'DOCKER_%s_IMAGE' % i.upper() for i in images]
    return all(k in os.environ for k in keys)


# Define custom checks for our environment.
@check('docker', 'We can talk to Docker')
def has_docker():
    if 'SKIP_DOCKER_TESTS' in os.environ:
        return False

    from vcttesting.docker import Docker, params_from_env

    url, tls = params_from_env(os.environ)

    tf = tempfile.NamedTemporaryFile()
    tf.close()
    d = Docker(tf.name, url, tls=tls)
    return d.is_alive()


@check('hgmodocker', 'Require hgmo Docker pieces')
def has_hgmodocker():
    images = (
        'ldap',
        'hgmaster',
        'hgweb',
        'pulse',
    )
    return has_docker() and have_docker_images(images)


@check('mozreviewdocker', 'Require mozreview Docker pieces')
def has_mozreviewdocker():
    images = (
        'bmoweb',
        'hgrb',
        'hgweb',
        'ldap',
        'pulse',
        'rbweb',
        'treestatus',
    )
    return has_docker() and have_docker_images(images)


@check('eslint', 'Require eslint')
def has_eslint():
    from distutils.spawn import find_executable
    return find_executable('eslint') is not None

@check('vcsreplicator', 'vcsreplicator Python modules')
def has_vcsreplicator():
    try:
        from vcsreplicator.config import Config
        return True
    except ImportError:
        return False

@check('watchman', 'Require watchman')
def has_watchman():
    from distutils.spawn import find_executable
    return find_executable('watchman') is not None


@check('bmodocker', 'Require BMO Docker pieces')
def has_bmodocker():
    return has_docker() and have_docker_images(['bmoweb'])


@check('internet', 'Require internet connectivity')
def has_internet():
    try:
        import socket
        host = socket.gethostbyname('www.mozilla.org')
        socket.create_connection((host, 80,), 2)
        return True

    except OSError:
        return False


require(sys.argv[1:])
