#!/usr/bin/env python

# Script to run the Jenkins job.

import os
import subprocess
import sys

HERE = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

VAGRANT = None

# ci.mozilla.org requires the vagrant from /opt/vagrant/bin to work.
# TODO this should be facilitated with proper environment variables.
for path in ['/opt/vagrant/bin/vagrant'] + os.environ['PATH'].split(':'):
    candidate = os.path.join(path, 'vagrant')
    if os.path.exists(candidate):
        VAGRANT = candidate
        break

if not VAGRANT:
    print('vagrant not found')
    sys.exit(1)

if 'BUILD_NUMBER' not in os.environ:
    print('BUILD_NUMBER not defined in environment. Are you running '
            'inside Jenkins?')
    sys.exit(1)

CWD = os.getcwd()

LAST_BUILD_PATH = os.path.join(CWD, 'last-good-build')
BUILD_NUMBER = int(os.environ['BUILD_NUMBER'])

last_good_build = None
if os.path.exists(LAST_BUILD_PATH):
    with open(LAST_BUILD_PATH, 'rb') as fh:
        last_good_build = int(fh.read().strip())

# If the last build failed, we destroy our Vagrant environment and rebuild from
# scratch in case things are in an inconsistent state. This is a bit hacky,
# but is the easiest solution to a complicated problem.
if last_good_build is None or BUILD_NUMBER > last_good_build + 1:
    print('Last build was bad. Blowing away virtual machine just in case.')
    subprocess.check_call([VAGRANT, 'destroy', '-f'], cwd=HERE)

subprocess.check_call([VAGRANT, 'up', '--provision'], cwd=HERE)

res = subprocess.call([VAGRANT, 'ssh', '--', '/version-control-tools/testing/jenkins/run.sh'],
    cwd=HERE)

if res == 0:
    with open(LAST_BUILD_PATH, 'wb') as fh:
        fh.write('%d' % BUILD_NUMBER)

subprocess.check_call([VAGRANT, 'halt'], cwd=HERE)

sys.exit(res)
