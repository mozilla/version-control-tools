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

HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))

# We import Mercurial's own ``hghave.py`` so we can declare our own checks.
HGHAVE_PY = os.path.join(REPO_ROOT, 'pylib', 'mercurial-support', 'hghave.py')
with open(HGHAVE_PY) as f:
    exec(f.read())


def have_docker_images(images):
    from vcttesting.docker import Docker, params_from_env

    url, tls = params_from_env(os.environ)

    d = Docker(url, tls=tls)
    for image in images:
        try:
            d.client.images.get("%s:%s" % (image, image))
        except Exception:
            return False

    return True


# Define custom checks for our environment.
@check('docker', 'We can talk to Docker')
def has_docker():
    if 'SKIP_DOCKER_TESTS' in os.environ:
        return False

    from vcttesting.docker import Docker, params_from_env

    url, tls = params_from_env(os.environ)

    d = Docker(url, tls=tls)
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


@check('internet', 'Require internet connectivity')
def has_internet():
    try:
        import socket
        host = socket.gethostbyname('www.mozilla.org')
        socket.create_connection((host, 80,), 2)
        return True

    except OSError:
        return False


@check('motoserver', 'moto AWS mock server')
def has_s3():
    '''Assert the boto3 mock library `moto` is available,
    as well as the `Flask` dependency which enables running
    a mock S3 server
    '''
    try:
        import moto
        moto.mock_s3

        import flask
        flask.Flask

        import simplejson
        simplejson.__version__

        return True
    except (ImportError, AttributeError):
        pass
    return False

require(sys.argv[1:])
