#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile


HERE = pathlib.Path(__file__).parent
PYTHON = HERE / 'python'
REQUIREMENTS_IN = PYTHON / 'requirements.in'
REQUIREMENTS_TXT = PYTHON / 'requirements.txt'

with tempfile.TemporaryDirectory() as tempd:
    subprocess.run([
        'pip',
        'download',
        '-r', '%s' % REQUIREMENTS_TXT,
        '--dest', '%s' % tempd,
        '--no-binary', ':all',
        '--disable-pip-version-check'])

    for entry in os.scandir(tempd):
        base, ext = os.path.splitext(entry.name)
        if ext == '.whl':
            # Wheels would extract into a directory with the name of the
            # package, but we want the platform signifiers, minus the version
            # number.
            # Wheel filenames look like:
            #
            # {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-
            # {platform tag}
            bits = base.split('-')

            if base.endswith('-py2.py3-none-any'):
                bits.pop()
                bits.pop()
                bits.pop()

            # Remove the version number.
            bits.pop(1)

            target = PYTHON / '-'.join(bits)

            if target.exists():
                shutil.rmtree(target)

            target.mkdir()

            with zipfile.ZipFile(entry.path, 'r') as zf:
                for name in zf.namelist():
                    p = pathlib.PurePosixPath(name)

                    if '.dist-info' in p.parts[0]:
                        if p.parts[1] != 'LICENSE.txt':
                            continue

                        dest = target / p.parts[1]
                        with dest.open('wb') as fh:
                            fh.write(zf.read(name))
                    else:
                        zf.extract(name, target)

        else:
            print('support for %s files not implemented' % ext)
            sys.exit(1)
