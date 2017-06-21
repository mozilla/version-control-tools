# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import subprocess


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def get_and_write_vct_node():
    hg = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'hg')
    env = dict(os.environ)
    env['HGRCPATH'] = '/dev/null'
    args = [hg, '-R', ROOT, 'log', '-r', '.', '-T', '{node|short}']
    with open(os.devnull, 'wb') as null:
        node = subprocess.check_output(args, env=env, cwd='/', stderr=null)

    with open(os.path.join(ROOT, '.vctnode'), 'wb') as fh:
        fh.write(node)

    return node
