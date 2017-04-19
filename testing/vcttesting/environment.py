# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import errno
import os
import subprocess


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CREATE_VIRTUALENV = os.path.join(ROOT, 'testing', 'create-virtualenv')


def create_virtualenv(name):
    path = os.path.join(ROOT, 'venv', name)

    try:
        os.makedirs(os.path.dirname(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    if os.name == 'nt':
        pip = os.path.join(path, 'Scripts', 'pip.exe')
        activate = os.path.join(path, 'Scripts', 'activate')
    else:
        pip = os.path.join(path, 'bin', 'pip')
        activate = os.path.join(path, 'bin', 'activate')

    res = {
        'path': path,
        'pip': pip,
        'activate': activate,
    }

    env = dict(os.environ)
    env['ROOT'] = ROOT
    env['VENV'] = path

    if not os.path.exists(path):
        subprocess.check_call([CREATE_VIRTUALENV, path], env=env)

    return res


def process_pip_requirements(venv, requirements):
    args = [
        venv['pip'], 'install', '--upgrade', '--require-hashes',
        '-r', os.path.join(ROOT, requirements),
    ]
    subprocess.check_call(args)


def install_editable(venv, relpath):
    args = [
        venv['pip'], 'install', '--no-deps', '--editable',
        os.path.join(ROOT, relpath)
    ]
    subprocess.check_call(args)


def create_vcssync():
    """Create an environment used for testing VCSSync."""
    venv = create_virtualenv('vcssync')
    process_pip_requirements(venv, 'vcssync/test-requirements.txt')
    install_editable(venv, 'testing')
    install_editable(venv, 'vcssync')

    return venv
