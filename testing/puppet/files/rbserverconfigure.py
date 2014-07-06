# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

path = sys.argv[1]
path = os.path.abspath(path)

sys.path.insert(0, path)

manage = [sys.executable, '-m', 'reviewboard.manage']

args = ['/home/reviewboard/venv/bin/rb-site']

if os.path.exists(path):
    args.append('upgrade')
else:
    args.append('install')

args.extend([
    path,
    '--noinput',
    '--domain-name=localhost',
    '--site-root=/',
    '--db-type=mysql',
    '--db-name=reviewboard',
    '--db-user=reviewboard',
    '--db-pass=reviewboard',
    '--cache-type=file',
    '--cache-info=/home/reviewboard/cache',
    '--web-server-type=apache',
    '--python-loader=wsgi',
])

if not os.path.exists(path):
    args.extend([
        '--admin-user=testadmin',
        '--admin-password=password',
        '--admin-email=testadmin@example.com',
    ])

subprocess.check_call(args)

conf_dir = os.path.join(path, 'conf')
os.chdir(conf_dir)

subprocess.check_call(manage + ['enable-extension',
    'rbbz.extension.BugzillaExtension'],
    cwd=conf_dir)

subprocess.check_call(manage + ['enable-extension',
    'rbmozui.extension.RBMozUI'],
    cwd=conf_dir)
