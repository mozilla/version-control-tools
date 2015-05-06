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

# Define custom checks for our environment.
@check('docker', 'We can talk to Docker')
def has_docker():
    from vcttesting.docker import Docker, params_from_env

    url, tls = params_from_env(os.environ)

    tf = tempfile.NamedTemporaryFile()
    tf.close()
    d = Docker(tf.name, url, tls=tls)
    return d.is_alive()

def hgversion():
    v = os.environ['HGVERSION']
    v = v.split('+')[0]
    v = v.split('-')[0]
    return tuple(int(i) for i in v.split('.'))

@check('hg31+', 'Running with Mercurial 3.1+')
def has_hg_31_plus():
    v = tuple(hgversion()[0:2])
    return v >= (3, 1)

@check('hg32+', 'Running with Mercurial 3.2+')
def has_hg32_plus():
    v = tuple(hgversion()[0:2])
    return v >= (3, 2)

@check('hg33+', 'Running with Mercurial 3.3+')
def has_hg33_plus():
    v = tuple(hgversion()[0:2])
    return v >= (3, 3)

# Now we reimplement the command line syntax of the CLI hghave script.
failures = 0

def error(msg):
    global failures
    sys.stderr.write('%s\n' % msg)
    failures += 1

for feature in sys.argv[1:]:
    negate = feature.startswith('no-')
    if negate:
        feature = feature[3:]

    if feature not in checks:
        error('skipped: unknown feature: ' + feature)
        sys.exit(2)

    check, desc = checks[feature]
    try:
        available = check()
    except Exception as e:
        error('hghave check failed: %s' % feature)
        continue

    if not negate and not available:
        error('skipped: missing feature: %s' % desc)
    elif negate and available:
        error('skipped: system supports %s' % desc)

if failures:
    sys.exit(1)

sys.exit(0)
