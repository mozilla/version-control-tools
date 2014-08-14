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

CWD = os.getcwd()

subprocess.check_call([VAGRANT, 'up'], cwd=HERE)

res = subprocess.call([VAGRANT, 'ssh', '--', '/version-control-tools/testing/jenkins/run.sh'],
    cwd=HERE)

subprocess.check_call([VAGRANT, 'halt'], cwd=HERE)

sys.exit(res)
