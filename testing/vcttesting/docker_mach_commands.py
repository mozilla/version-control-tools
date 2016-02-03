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

    @Command('build-mozreview', category='docker',
        description='Build Docker images required for MozReview')
    def build_mozreview(self):
        self.d.build_mozreview(verbose=True)

    @Command('start-bmo', category='docker',
        description='Start a bugzilla.mozilla.org instance')
    @CommandArgument('cluster', help='Name to give to this instance')
    @CommandArgument('http_port',
        help='HTTP port the server should be exposed on')
    @CommandArgument('--web-id-file',
        help='File to store the bmoweb container ID in')
    def start_bmo(self, cluster, http_port, web_id_file=None):
        web_image = os.environ.get('DOCKER_BMO_WEB_IMAGE')

        res = self.d.start_bmo(cluster=cluster,
                http_port=http_port,
                web_image=web_image)

        if web_id_file:
            with open(web_id_file, 'wb') as fh:
                fh.write(res['web_id'])

    @Command('stop-bmo', category='docker',
        description='Stop a bugzilla.mozilla.org instance')
    @CommandArgument('cluster', help='Name of instance to stop')
    def stop_bmo(self, cluster):
        self.d.stop_bmo(cluster)

    @Command('build', category='docker',
             description='Build a single image')
    @CommandArgument('name', help='Name of image to build')
    def build(self, name):
        self.d.ensure_built(name, verbose=True)

    @Command('build-all', category='docker',
             description='Build all images')
    def build_all(self):
        self.d.build_all_images(verbose=True)

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

    @Command('build-mercurial-rpms', category='docker',
        description='Build RPMs for Mercurial')
    @CommandArgument('destdir', help='Directory in which to save RPMs')
    def build_rpms(self, destdir):
        for filename, data in self.d.build_mercurial_rpms().items():
            outfile = os.path.join(destdir, filename)
            with open(outfile, 'wb') as fh:
                fh.write(data)
            print('Wrote %s' % outfile)

    @Command('generate-hgweb-mozbuild-files', category='docker',
             description='Generate files for a moz.build evaluation environment')
    @CommandArgument('dest', help='Directory to write files to')
    def generate_hgweb_chroot(self, dest):
        from vcttesting.hgmo import get_hgweb_mozbuild_chroot

        if not os.path.exists(dest):
            os.mkdir(dest)

        chroot, executable = get_hgweb_mozbuild_chroot(self.d)

        with open(os.path.join(dest, 'chroot.tar.gz'), 'w') as fh:
            fh.write(chroot)
            print('wrote %d bytes for chroot archive' % len(chroot))

        with open(os.path.join(dest, 'mozbuild-eval'), 'w') as fh:
            fh.write(executable)
            print('wrote %d bytes for mozbuild-eval' % len(executable))

        print('wrote files to %s' % dest)

    # This should ideally be elsewhere. This was introduced at a time when
    # start-bmo didn't track the bmoweb container ID explicitly.
    @Command('create-bugzilla-api-key', category='docker',
             description='Create and print an API key for a user')
    @CommandArgument('cid', help='bmoweb container ID')
    @CommandArgument('user', help='User to create key for')
    def create_api_key(self, cid, user):
        print(self.d.execute(cid, [
            '/var/lib/bugzilla/bugzilla/scripts/issue-api-key.pl',
            user,
        ], stdout=True).strip())
