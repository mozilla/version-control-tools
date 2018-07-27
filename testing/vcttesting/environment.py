# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import errno
import os
import shutil
import subprocess


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CREATE_VIRTUALENV = os.path.join(ROOT, 'testing', 'create-virtualenv')


SITECUSTOMIZE = b'''
import os

if os.environ.get('CODE_COVERAGE', False):
    import uuid
    import coverage

    covpath = os.path.join(os.environ['COVERAGE_DIR'], 'data',
                           'coverage.%s' % uuid.uuid1())
    cov = coverage.Coverage(data_file=covpath, auto_data=True, branch=True)
    cov._warn_no_data = False
    cov._warn_unimported_source = False
    cov.start()
'''


def create_virtualenv(name):
    path = os.path.join(ROOT, 'venv', name)

    try:
        os.makedirs(os.path.dirname(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    if os.name == 'nt':
        bin_dir = os.path.join(path, 'Scripts')
        pip = os.path.join(bin_dir, 'pip.exe')
        python = os.path.join(bin_dir, 'python.exe')
        activate = os.path.join(bin_dir, 'activate')
    else:
        bin_dir = os.path.join(path, 'bin')
        pip = os.path.join(bin_dir, 'pip')
        python = os.path.join(bin_dir, 'python')
        activate = os.path.join(bin_dir, 'activate')

    res = {
        'path': path,
        'bin_dir': bin_dir,
        'pip': pip,
        'python': python,
        'activate': activate,
        'activate_this': os.path.join(bin_dir, 'activate_this.py'),
    }

    env = dict(os.environ)
    env['ROOT'] = ROOT
    env['VENV'] = path

    if not os.path.exists(res['pip']):
        subprocess.check_call([CREATE_VIRTUALENV, path], env=env)

    # Install a sitecustomize.py that starts code coverage if an environment
    # variable is set.
    with open(os.path.join(bin_dir, 'sitecustomize.py'), 'wb') as fh:
        fh.write(SITECUSTOMIZE)

    return res


def activate_virtualenv(venv):
    """Activate a virtualenv in the current Python process."""
    execfile(venv['activate_this'], dict(__file__=venv['activate_this']))


def process_pip_requirements(venv, requirements):
    args = [
        venv['pip'], 'install', '--upgrade', '--require-hashes',
        '-r', os.path.join(ROOT, requirements),
    ]
    subprocess.check_call(args)


def install_editable(venv, relpath, extra_env=None):
    args = [
        venv['pip'], 'install', '--no-deps', '--editable',
        os.path.join(ROOT, relpath)
    ]

    env = dict(os.environ)
    env.update(extra_env or {})

    subprocess.check_call(args, env=env)


def install_mercurials(venv, hg):
    """Install supported Mercurial versions in a central location."""
    VERSIONS = [
        '4.3.3',
        '4.4.2',
        '4.5.3',
        '4.6.2',
        '@',
    ]

    hg_dir = os.path.join(ROOT, 'venv', 'hg')
    mercurials = os.path.join(venv['path'], 'mercurials')

    # Setting HGRCPATH to an empty value stops the global and user hgrc from
    # being loaded. These could interfere with behavior we expect from
    # vanilla Mercurial.
    hg_env = dict(os.environ)
    hg_env['HGRCPATH'] = ''

    # Ensure a Mercurial clone is present and up to date.
    if not os.path.isdir(hg_dir):
        print('cloning Mercurial repository to %s' % hg_dir)
        subprocess.check_call([hg, 'clone',
                               'https://www.mercurial-scm.org/repo/hg',
                               hg_dir],
                              cwd='/', env=hg_env)

    subprocess.check_call([hg, 'pull'], cwd=hg_dir, env=hg_env)

    try:
        os.makedirs(mercurials)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Remove old versions.
    for p in os.listdir(mercurials):
        if p in ('.', '..'):
            continue

        if p not in VERSIONS:
            print('removing old, unsupported Mercurial version: %s' % p)
            shutil.rmtree(os.path.join(mercurials, p))

    for v in VERSIONS:
        dest = os.path.join(mercurials, v)

        # Always reinstall @ because it isn't a static tag.
        if v == '@' and os.path.exists(dest):
            shutil.rmtree(dest)

        if os.path.exists(dest):
            continue

        print('installing Mercurial %s to %s' % (v, dest))
        try:
            subprocess.check_output([hg, 'update', v], cwd=hg_dir, env=hg_env,
                                    stderr=subprocess.STDOUT)
            # We don't care about support files, which only slow down
            # installation. So install-bin is a suitable target.
            subprocess.check_output(['make', 'install-bin',
                                     'PREFIX=%s' % dest,
                                     'PYTHON=%s' % venv['python']],
                                    cwd=hg_dir, env=hg_env,
                                    stderr=subprocess.STDOUT)
            subprocess.check_output([hg, '--config', 'extensions.purge=',
                                     'purge', '--all'],
                                    cwd=hg_dir, env=hg_env,
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print('error installing: %s' % e.output)
            raise Exception('could not install Mercurial')


def docker_client():
    """Attempt to obtain a Docker client.

    Returns a client on success. None on failure.
    """
    from .docker import (
        Docker,
        params_from_env,
    )

    state_file = os.path.join(ROOT, '.dockerstate')
    docker_url, tls = params_from_env(os.environ)

    d = Docker(state_file, docker_url, tls=tls)

    return d if d.is_alive() else None


def create_hgdev(docker_bmo=False):
    """Create an environment used for hacking on Mercurial extensions."""
    venv = create_virtualenv('hgdev')

    if docker_bmo:
        reqs = 'testing/requirements-hgdev-docker.txt'
    else:
        reqs = 'testing/requirements-hgdev.txt'

    process_pip_requirements(venv, reqs)
    install_editable(venv, 'hghooks')
    install_editable(venv, 'pylib/Bugsy')
    install_editable(venv, 'pylib/mozhg')
    install_editable(venv, 'pylib/mozhginfo')
    install_editable(venv, 'pylib/mozautomation')
    install_editable(venv, 'testing')

    install_mercurials(venv, hg=os.path.join(venv['bin_dir'], 'hg'))

    if docker_bmo:
        activate_virtualenv(venv)
        docker = docker_client()

        if docker:
            docker.build_bmo(verbose=True)
        else:
            print('Docker not available; cannot build BMO Docker image')

        print('attempting to builder bugzilla.mozilla.org Docker image')

    return venv


def create_vcssync():
    """Create an environment used for testing VCSSync."""
    venv = create_virtualenv('vcssync')
    process_pip_requirements(venv, 'vcssync/test-requirements.txt')
    install_editable(venv, 'pylib/mozautomation')
    install_editable(venv, 'testing')
    install_editable(venv, 'vcssync',
                     extra_env={'VCSSYNC_ENABLE_TESTING_COMMANDS': '1'})

    return venv


def create_xchannel():
    """Create an environment used for testing VCSSync."""
    venv = create_virtualenv('cross-channel-l10n')
    process_pip_requirements(venv, 'cross-channel-l10n/test-requirements.txt')
    install_editable(venv, 'testing')
    install_editable(venv, 'cross-channel-l10n')

    return venv


if __name__ == '__main__':
    import sys

    # This is a hack to support create-test-environment.
    if sys.argv[1] == 'install-mercurials':
        venv = {
            'path': os.path.join(ROOT, 'venv'),
            'python': os.path.join(ROOT, 'venv', 'bin', 'python'),
        }
        # PATH has global virtualenv activated.
        install_mercurials(venv, hg='hg')
