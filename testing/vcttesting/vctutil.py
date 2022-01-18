# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import subprocess
import sys
import yaml


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def decrypt_sops_files():
    '''Decrypt all files with encrypted keys in the repo.

    All files found in the list under the "files" key of the
    `.sops.yaml` file will have all secrets with an
    "_encrypted" suffix decrypted.
    '''
    with open(os.path.join(ROOT, '.sops.yaml')) as f:
        files = yaml.safe_load(f).get('files')

    if not files:
        return

    for path in files:
        subprocess.check_call([
            'sops', '--in-place', '--decrypt', path,
        ], cwd=ROOT)


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
    if not os.path.exists(os.path.join(ROOT, '.hg')):
        raise Exception('version-control-tools directory must be a Mercurial '
                        'checkout')

    env = dict(os.environ)
    env['HGRCPATH'] = '/dev/null'
    args = [hg_executable(), '-R', ROOT, 'log', '-r', '.', '-T', '{node|short}']
    with open(os.devnull, 'wb') as null:
        node = subprocess.check_output(args, env=env, cwd='/', stderr=null)

    with open(os.path.join(ROOT, '.vctnode'), 'wb') as fh:
        fh.write(node)

    return node
