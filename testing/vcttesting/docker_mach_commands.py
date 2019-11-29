# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

from vcttesting.docker import (
    Docker,
    params_from_env,
)


ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))


@CommandProvider
class DockerCommands(object):
    def __init__(self, context):
        if 'DOCKER_STATE_FILE' in os.environ:
            state_file = os.environ['DOCKER_STATE_FILE']

        # When running from Mercurial tests, use a per-test state file.
        # We can't use HGTMP because it is shared across many tests. We
        # use HGRCPATH as a base, since it is in a test-specific directory.
        elif 'HGRCPATH' in os.environ:
            state_file = os.path.join(os.path.dirname(os.environ['HGRCPATH']),
                                     '.dockerstate')
        else:
            state_file = os.path.join(ROOT, '.dockerstate')

        docker_url, tls = params_from_env(os.environ)
        d = Docker(state_file, docker_url, tls=tls)

        if not d.is_alive():
            print('Docker is not available!')
            sys.exit(1)

        self.d = d

    @Command('build-hgmo', category='docker',
        description='Build hg.mozilla.org Docker images')
    def build_hgmo(self):
        self.d.build_hgmo(verbose=True)

    @Command('build', category='docker',
             description='Build a single image')
    @CommandArgument('name', help='Name of image to build')
    def build(self, name):
        self.d.ensure_built(name, verbose=True)

    @Command('build-all', category='docker',
             description='Build all images')
    @CommandArgument('--forks', type=int,
                     help='Number of parallel build processes to use. '
                          '(default=unlimited)')
    def build_all(self, forks=None):
        self.d.build_all_images(verbose=True, max_workers=forks)

    @Command('run-ansible', category='docker',
             description='Run Ansible to produce a Docker image')
    @CommandArgument('playbook',
                     help='Name of Ansible playbook to execute')
    @CommandArgument('--builder',
                     help='Docker build to start from')
    @CommandArgument('--start-image',
                     help='Existing Docker image to operate on')
    @CommandArgument('--repository',
                     help='Tag the produced image with this repository')
    def run_ansible(self, playbook, builder=None, start_image=None,
                    repository=None):
        self.d.run_ansible(playbook, builder=builder, start_image=start_image,
                           repository=repository, verbose=True)

    @Command('prune-images', category='docker',
        description='Prune old Docker images')
    def prune_images(self):
        self.d.prune_images()
