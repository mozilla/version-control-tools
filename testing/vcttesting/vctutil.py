# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import subprocess
import sys


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def hg_executable():
    if 'VIRTUAL_ENV' in os.environ:
        venv = os.environ['VIRTUAL_ENV']
    # Virtualenv activated by Python itself, not from shell.
    elif hasattr(sys, 'real_prefix'):
        venv = sys.prefix
    else:
        venv = os.path.join(ROOT, 'venv')

    if os.name == 'nt':
        return os.path.join(venv, 'Scripts', 'hg.exe')
    else:
        return os.path.join(venv, 'bin', 'hg')


def get_and_write_vct_node():
    env = dict(os.environ)
    env['HGRCPATH'] = '/dev/null'
    args = [hg_executable(), '-R', ROOT, 'log', '-r', '.', '-T', '{node|short}']
    with open(os.devnull, 'wb') as null:
        node = subprocess.check_output(args, env=env, cwd='/', stderr=null)

    with open(os.path.join(ROOT, '.vctnode'), 'wb') as fh:
        fh.write(node)

    return node
