# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

from __future__ import absolute_import

import base64
from collections import deque
import docker
import json
import os
import pickle
import re
import requests
import ssl
import subprocess
import sys
import tarfile
import tempfile
import time
import urlparse
import uuid

from docker.errors import APIError as DockerAPIError
from contextlib import contextmanager
from io import BytesIO

import concurrent.futures as futures
from coverage.data import CoverageData

from .util import (
    get_and_write_vct_node,
    wait_for_amqp,
    wait_for_http,
    wait_for_ssh,
)


HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, '..', 'docker'))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def rsync(*args):
    prog = None
    for path in os.environ['PATH'].split(':'):
        candidate = os.path.join(path, 'rsync')
        if os.path.exists(candidate):
            prog = candidate
            break

    if not prog:
        raise Exception('Could not find rsync program')

    subprocess.check_call([prog] + list(args), cwd='/')


class DockerNotAvailable(Exception):
    """Error raised when Docker is not available."""


def params_from_env(env):
    """Obtain Docker connect parameters from the environment.

    This returns a tuple that should be used for base_url and tls arguments
    of Docker.__init__.
    """
    host = env.get('DOCKER_HOST', None)
    tls = False

    if env.get('DOCKER_TLS_VERIFY'):
        tls = True

    # This is likely encountered with boot2docker.
    cert_path = env.get('DOCKER_CERT_PATH')
    if cert_path:
        ca_path = os.path.join(cert_path, 'ca.pem')
        tls_cert_path = os.path.join(cert_path, 'cert.pem')
        tls_key_path = os.path.join(cert_path, 'key.pem')

        # Hostnames will attempt to be verified by default. We don't know what
        # the hostname should be, so don't attempt it.
        tls = docker.tls.TLSConfig(client_cert=(tls_cert_path, tls_key_path),
                ssl_version=ssl.PROTOCOL_TLSv1, ca_cert=ca_path, verify=True,
                assert_hostname=False)

    # docker-py expects the protocol to have something TLS in it. tcp:// won't
    # work. Hack around it until docker-py works as expected.
    if tls and host:
        if host.startswith('tcp://'):
            host = host.replace('tcp://', 'https://')

    return host, tls


class Docker(object):
    def __init__(self, state_path, url, tls=False):
        self._ddir = DOCKER_DIR
        self._state_path = state_path
        self.state = {
            'clobber-bmobootstrap': None,
            'clobber-bmofetch': None,
            'images': {},
            'containers': {},
            'last-bmodb-id': None,
            'last-bmoweb-id': None,
            'last-pulse-id': None,
            'last-rbweb-id': None,
            'last-bmodb-bootstrap-id': None,
            'last-bmoweb-bootstrap-id': None,
            'last-rbweb-bootstrap-id': None,
            'last-autolanddb-id': None,
            'last-autoland-id': None,
            'last-hgmaster-id': None,
            'last-hgweb-id': None,
            'last-ldap-id': None,
            'last-vct-id': None,
            'vct-cid': None,
        }

        if os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                self.state = json.load(fh)

        keys = (
            'clobber-bmobootstrap',
            'clobber-bmofetch',
            'last-bmodb-id',
            'last-bmoweb-id',
            'last-pulse-id',
            'last-rbweb-id',
            'last-bmodb-bootstrap-id',
            'last-bmoweb-bootstrap-id',
            'last-rbweb-bootstrap-id',
            'last-autolanddb-id',
            'last-autoland-id',
            'last-hgmaster-id',
            'last-hgweb-id',
            'last-ldap-id',
            'last-vct-id',
            'vct-cid',
        )
        for k in keys:
            self.state.setdefault(k, None)

        self.client = docker.Client(base_url=url, tls=tls)

        # Try to obtain a network hostname for the Docker server. We use this
        # for determining where to look for opened ports.
        # This is a bit complicated because Docker can be running from a local
        # socket or or another host via something like boot2docker.
        # TODO look at network info for Docker and extract IP address instead.
        docker_url = urlparse.urlparse(self.client.base_url)
        self.docker_hostname = docker_url.hostname
        if 'unix' in docker_url.scheme:
            self.docker_hostname = 'localhost'

    def is_alive(self):
        """Whether the connection to Docker is alive."""
        # This is a layering violation with docker.client, but meh.
        try:
            self.client._get(self.client._url('/version'), timeout=5)
            return True
        except requests.exceptions.RequestException as e:
            return False

    def _get_vct_files(self):
        """Obtain all the files in the version-control-tools repo.

        Returns a dict of relpath to full path.
        """
        hg = os.path.join(ROOT, 'venv', 'bin', 'hg')
        env = dict(os.environ)
        env['HGRCPATH'] = '/dev/null'
        args = [hg, '-R', ROOT, 'locate']
        with open(os.devnull, 'wb') as null:
            output = subprocess.check_output(args, env=env, cwd='/',
                                             stderr=null)

        paths = {}
        for f in output.splitlines():
            full = os.path.join(ROOT, f)
            # Filter out files that have been removed in the working
            # copy but haven't been committed.
            if os.path.exists(full):
                paths[f] = full

        return paths

    def clobber_needed(self, name):
        """Test whether a clobber file has been touched.

        We periodically need to force certain actions to occur. There is a
        "clobber" mechanism to facilitate this.

        There are various ``clobber.<name>`` files on the filesystem. When
        the files are touched, it signals a clobber is required.

        This function answers the question of whether a clobber is required
        for a given action. Returns True if yes, False otherwise.
        """
        path = os.path.join(ROOT, 'testing', 'clobber.%s' % name)
        key = 'clobber-%s' % name
        oldmtime = self.state[key]
        newmtime = os.path.getmtime(path)

        if oldmtime is None or newmtime > oldmtime:
            self.state[key] = int(time.time())
            return True

        return False

    def ensure_built(self, name, verbose=False, use_last=False):
        """Ensure a Docker image from a builder directory is built and up to date.

        This function is docker build++. Under the hood, it talks to the same
        ``build`` Docker API. However, it does one important thing differently:
        it builds the context archive manually.

        We supplement all contexts with the content of the source in this
        repository related to building Docker containers. This is done by
        scanning the Dockerfile for references to extra files to include.

        If a line in the Dockerfile has the form ``# %include <path>``,
        the relative path specified on that line will be matched against
        files in the source repository and added to the context under the
        path ``extra/vct/``. If an entry ends in a ``/``, we add all files
        under that directory. Otherwise, we assume it is a literal match and
        only add a single file.

        This added content can be ``ADD``ed to the produced image inside the
        Dockerfile. If the content changes, the Docker image ID changes and the
        cache is invalidated. This effectively allows downstream consumers to
        call ``ensure_built()`` as there *is the image up to date* check.

        If ``use_last`` is true, the last built image will be returned, if
        available.
        """
        if use_last:
            for image in reversed(self.client.images()):
                for repotag in image['RepoTags']:
                    repo, tag = repotag.split(':', 1)
                    if repo == name:
                        return image['Id']

        p = os.path.join(self._ddir, 'builder-%s' % name)
        if not os.path.isdir(p):
            raise Exception('Unknown Docker builder name: %s' % name)

        vct_paths = []
        with open(os.path.join(p, 'Dockerfile'), 'rb') as fh:
            for line in fh:
                line = line.rstrip()
                if not line.startswith('# %include'):
                    continue

                vct_paths.append(line[len('# %include '):])

        # We build the build context for the image manually because we need to
        # include things outside of the directory containing the Dockerfile.
        buf = BytesIO()
        tar = tarfile.open(mode='w', fileobj=buf)

        for root, dirs, files in os.walk(p):
            for f in files:
                if f == '.dockerignore':
                    raise Exception('.dockerignore not currently supported!')

                full = os.path.join(root, f)
                rel = full[len(p)+1:]
                tar.add(full, arcname=rel)

        if vct_paths:
            # We grab the set of tracked files in this repository.
            vct_files = sorted(self._get_vct_files().keys())
            added = set()
            for p in vct_paths:
                ap = os.path.join(ROOT, p)
                if not os.path.exists(ap):
                    raise Exception('specified path not under version '
                                    'control: %s' % p)
                if p.endswith('/'):
                    for f in vct_files:
                        if not f.startswith(p) and p != '/':
                            continue
                        full = os.path.join(ROOT, f)
                        rel = 'extra/vct/%s' % f
                        if full in added:
                            continue
                        tar.add(full, rel)
                else:
                    full = os.path.join(ROOT, p)
                    if full in added:
                        continue
                    rel = 'extra/vct/%s' % p
                    tar.add(full, rel)

        tar.close()

        # Need to seek to beginning so .read() inside docker.client will return
        # data.
        buf.seek(0)

        # The API here is wonky, possibly due to buggy behavior in
        # docker.client always setting stream=True if version > 1.8.
        # We assume this is a bug that will change behavior later and work
        # around it by ensuring consistent behavior.
        for stream in self.client.build(fileobj=buf, custom_context=True,
                                        rm=True, stream=True):
            s = json.loads(stream)
            if 'stream' not in s:
                continue

            s = s['stream']
            if verbose:
                # s has newlines, so don't go through print().
                sys.stdout.write('%s> %s' % (name, s))
            match = re.match('^Successfully built ([a-f0-9]{12})$', s.rstrip())
            if match:
                image = match.group(1)
                # There is likely a trailing newline.
                full_image = self.get_full_image(image.rstrip())

                # We only tag the image once to avoid redundancy.
                have_tag = False
                for i in self.client.images():
                    if i['Id'] == full_image:
                        for repotag in i['RepoTags']:
                            repo, tag = repotag.split(':')
                            if repo == name:
                                have_tag = True

                        break
                if not have_tag:
                    self.client.tag(full_image, name, str(uuid.uuid1()))

                return full_image

        raise Exception('Unable to confirm image was built')

    def ensure_images_built(self, names, ansibles=None, existing=None,
                            verbose=False, use_last=False):
        """Ensure that multiple images are built.

        ``names`` is a list of Docker images to build.
        ``ansibles`` describes how to build ansible-based images. Keys
        are repositories. Values are tuples of (playbook, builder). If an
        image in the specified repositories is found, we'll use it as the
        start image. Otherwise, we'll use the configured builder.

        If ``use_last`` is true, we will use the last built image instead
        of building a new one.
        """
        ansibles = ansibles or {}
        existing = existing or {}

        # Verify existing images actually exist.
        docker_images = self.all_docker_images()

        images = {k: v for k, v in existing.items() if v in docker_images}

        missing = (set(names) | set(ansibles.keys())) - set(images.keys())

        if not missing:
            return images

        ma = {k: ansibles[k] for k in missing if k in ansibles}
        start_images = {}
        for image in reversed(self.client.images()):
            for repotag in image['RepoTags']:
                repo, tag = repotag.split(':', 1)
                if repo in ma:
                    start_images[repo] = image['Id']

        def build(name, **kwargs):
            image = self.ensure_built(name, use_last=use_last, **kwargs)
            return name, image

        def build_ansible(f_builder, vct_cid, playbook, repository=None,
                          builder=None, start_image=None, verbose=False):

            if start_image and use_last:
                return repository, start_image

            # Wait for the builder image to be built.
            if f_builder:
                start_image = f_builder.result()
                builder = None

            image, repo, tag = self.run_ansible(playbook,
                                                repository=repository,
                                                builder=builder,
                                                start_image=start_image,
                                                vct_cid=vct_cid,
                                                verbose=verbose)
            return repository, image

        with self.vct_container(verbose=verbose) as vct_state, futures.ThreadPoolExecutor(len(missing)) as e:
            vct_cid = vct_state['Id']
            fs = []
            builder_fs = {}
            for n in sorted(missing):
                if n in names:
                    fs.append(e.submit(build, n, verbose=verbose))
                else:
                    playbook, builder = ansibles[n]
                    start_image = start_images.get(n)
                    if start_image:
                        builder = None

                    # Builders may be shared across images. This code it to
                    # ensure we only build the builder image once.
                    if builder:
                        bf = builder_fs.get(builder)
                        if not bf:
                            bf = e.submit(self.ensure_built,
                                          'ansible-%s' % builder,
                                          verbose=verbose)
                            builder_fs[builder] = bf
                    else:
                        bf = None

                    fs.append(e.submit(build_ansible, bf, vct_cid, playbook,
                                       repository=n, builder=builder,
                                       start_image=start_image,
                                       verbose=verbose))


            for f in futures.as_completed(fs):
                name, image = f.result()
                images[name] = image

        return images

    def run_ansible(self, playbook, repository=None,
                    builder=None, start_image=None, vct_image=None,
                    vct_cid=None, verbose=False):
        """Create an image with the results of Ansible playbook execution.

        This function essentially does the following:

        1. Obtain a starting image.
        2. Create and start a container with the content of v-c-t mounted
           in that container.
        3. Run the ansible playbook specified.
        4. Tag the resulting image.

        You can think of this function as an alternative mechanism for building
        Docker images. Instead of Dockerfiles, we use Ansible to "provision"
        our containers.

        You can provision containers either from scratch or incrementally.

        To build from scratch, specify a ``builder``. This corresponds to a
        directory in v-c-t that contains a Dockerfile specifying how to install
        Ansible in an image. e.g. ``centos6`` will be expanded to
        ``builder-ansible-centos6``.

        To build incrementally, specify a ``start_image``. This is an existing
        Docker image.

        One of ``builder`` or ``start_image`` must be specified. Both cannot be
        specified.
        """
        if not builder and not start_image:
            raise ValueError('At least 1 of "builder" or "start_image" '
                             'must be defined')
        if builder and start_image:
            raise ValueError('Only 1 of "builder" and "start_image" may '
                             'be defined')

        repository = repository or playbook

        if builder:
            full_builder = 'ansible-%s' % builder
            start_image = self.ensure_built(full_builder, verbose=verbose)

        # Docker imposes a limit of 127 stacked images, at which point an
        # error will be raised creating a new container. Since Ansible
        # containers are incremental images, it's only a matter of time before
        # this limit gets hit.
        #
        # When we approach this limit, walk the stack of images and reset the
        # base image to the first image built with Ansible. This ensures
        # some cache hits and continuation and prevents us from brushing into
        # the limit.
        history = self.client.history(start_image)
        if len(history) > 120:
            # Newest to oldest.
            for base in history:
                if base['CreatedBy'].startswith('/sync-and-build'):
                    start_image = base['Id']

        with self.vct_container(image=vct_image, cid=vct_cid, verbose=verbose) as vct_state:
            cmd = ['/sync-and-build', '%s.yml' % playbook]
            with self.create_container(start_image, command=cmd) as cid:
                output = deque(maxlen=20)
                self.client.start(cid, volumes_from=[vct_state['Name']])

                for s in self.client.attach(cid, stream=True, logs=True):
                    for line in s.splitlines():
                        output.append(line)
                        if verbose:
                            print('%s> %s' % (repository, line))

                state = self.client.inspect_container(cid)
                if state['State']['ExitCode']:
                    # This should arguably be part of the exception.
                    for line in output:
                        print('ERROR %s> %s' % (repository, line))
                    raise Exception('Ansible did not run on %s successfully' %
                                    repository)

                tag = str(uuid.uuid1())

                iid = self.client.commit(cid['Id'], repository=repository, tag=tag)['Id']
                iid = self.get_full_image(iid)
                return iid, repository, tag

    def build_hgmo(self, images=None, verbose=False, use_last=False):
        """Ensure the images for a hg.mozilla.org service are built.

        hg-master runs the ssh service while hg-slave runs hgweb. The mirroring
        and other bits should be the same as in production with the caveat that
        LDAP integration is probably out of scope.
        """
        images = self.ensure_images_built([
            'ldap',
        ], ansibles={
            'hgmaster': ('docker-hgmaster', 'centos6'),
            'hgweb': ('docker-hgweb', 'centos6'),
        }, existing=images, verbose=verbose, use_last=use_last)

        self.state['last-hgmaster-id'] = images['hgmaster']
        self.state['last-hgweb-id'] = images['hgweb']
        self.state['last-ldap-id'] = images['ldap']

        return images

    def build_mozreview(self, images=None, verbose=False, use_last=False):
        """Ensure the images for a MozReview service are built.

        bmoweb's entrypoint does a lot of setup on first run. This takes many
        seconds to perform and this cost is unacceptable for efficient test
        running. So, when we build the BMO images, we create throwaway
        containers and commit the results to a new image. This allows us to
        spin up multiple bmoweb containers very quickly.
        """
        state_images = self.state['images']

        images = self.ensure_images_built([
            'autolanddb',
            'autoland',
            'bmodb-volatile',
            'bmoweb',
            'ldap',
            'pulse',
        ], ansibles={
            'hgrb': ('docker-hgrb', 'centos6'),
            'rbweb': ('docker-rbweb', 'centos6'),
        }, existing=images, verbose=verbose, use_last=use_last)

        self.state['last-autolanddb-id'] = images['autolanddb']
        self.state['last-autoland-id'] = images['autoland']
        self.state['last-bmodb-id'] = images['bmodb-volatile']
        self.state['last-bmoweb-id'] = images['bmoweb']
        self.state['last-hgrb-id'] = images['hgrb']
        self.state['last-ldap-id'] = images['ldap']
        self.state['last-pulse-id'] = images['pulse']
        self.state['last-rbweb-id'] = images['rbweb']

        # The keys for the bootstrapped images are derived from the base
        # images they depend on. This means that if we regenerate a new
        # base image, the bootstrapped images will be regenerated.
        bmodb_bootstrapped_key = 'bmodb-bootstrapped:%s' % images['bmodb-volatile']
        bmoweb_bootstrapped_key = 'bmoweb-bootstrapped:%s:%s' % (
                images['bmodb-volatile'], images['bmoweb'])

        self.save_state()

        bmodb_bootstrap = state_images.get(bmodb_bootstrapped_key)
        bmoweb_bootstrap = state_images.get(bmoweb_bootstrapped_key)

        known_images = self.all_docker_images()
        if bmodb_bootstrap and bmodb_bootstrap not in known_images:
            bmodb_bootstrap = None
        if bmoweb_bootstrap and bmoweb_bootstrap not in known_images:
            bmoweb_bootstrap = None

        if (not bmodb_bootstrap or not bmoweb_bootstrap
            or self.clobber_needed('bmobootstrap')):
            bmodb_bootstrap, bmoweb_bootstrap = self._bootstrap_bmo(
                    images['bmodb-volatile'], images['bmoweb'])

        state_images[bmodb_bootstrapped_key] = bmodb_bootstrap
        state_images[bmoweb_bootstrapped_key] = bmoweb_bootstrap
        self.state['last-bmodb-bootstrap-id'] = bmodb_bootstrap
        self.state['last-bmoweb-bootstrap-id'] = bmoweb_bootstrap
        self.save_state()

        return {
            'autolanddb': images['autolanddb'],
            'autoland': images['autoland'],
            'bmodb': bmodb_bootstrap,
            'bmoweb': bmoweb_bootstrap,
            'hgrb': images['hgrb'],
            'ldap': images['ldap'],
            'pulse': images['pulse'],
            'rbweb': images['rbweb'],
        }

    def _bootstrap_bmo(self, db_image, web_image):
        """Build bootstrapped BMO images.

        BMO's first run time takes several seconds. It isn't practical to wait
        for this every time the containers start. So, we do the first run code
        once and commit the result to a new image.
        """
        db_id = self.client.create_container(
                db_image,
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']

        web_environ = {}

        if 'FETCH_BMO' in os.environ or self.clobber_needed('bmofetch'):
            web_environ['FETCH_BMO'] = '1'

        web_id = self.client.create_container(web_image,
                                              environment=web_environ)['Id']

        with self.start_container(db_id) as db_state:
            web_params = {
                'links': [(db_state['Name'], 'bmodb')],
                'port_bindings': {80: None},
            }
            with self.start_container(web_id, **web_params) as web_state:
                web_hostname, web_port = self._get_host_hostname_port(web_state, '80/tcp')
                print('waiting for containers to bootstrap')
                wait_for_http(web_hostname, web_port, path='xmlrpc.cgi',
                              extra_check_fn=self._get_assert_container_running_fn(web_id))

        db_unique_id = str(uuid.uuid1())
        web_unique_id = str(uuid.uuid1())

        print('committing bootstrapped images')

        # Save an image of the stopped containers.
        # We tag with a unique ID so we can identify all bootrapped images
        # easily from Docker's own metadata. We have to give a tag becaue
        # Docker will forget the repository name if a name image has only a
        # repository name as well.
        with futures.ThreadPoolExecutor(2) as e:
            db_future = e.submit(self.client.commit, db_id,
                                 repository='bmodb-volatile-bootstrapped',
                                 tag=db_unique_id)
            web_future = e.submit(self.client.commit, web_id,
                                  repository='bmoweb-bootstrapped',
                                  tag=web_unique_id)

        db_bootstrap = db_future.result()['Id']
        web_bootstrap = web_future.result()['Id']

        print('removing non-bootstrapped containers')

        with futures.ThreadPoolExecutor(2) as e:
            e.submit(self.client.remove_container, web_id)
            e.submit(self.client.remove_container, db_id)

        print('bootstrapped images created')

        return db_bootstrap, web_bootstrap

    def start_mozreview(self, cluster, http_port=80,
            hgrb_image=None, ldap_image=None, ldap_port=None, pulse_port=None,
            rbweb_port=None, db_image=None, web_image=None, pulse_image=None,
            rbweb_image=None, autolanddb_image=None, ssh_port=None,
            hg_port=None, autoland_image=None, autoland_port=None,
            verbose=False):

        start_ldap = False
        if ldap_port:
            start_ldap = True

        start_hgrb = False
        if ssh_port or hg_port:
            start_hgrb = True
            # We need LDAP for SSH logins to work.
            start_ldap = True

        start_pulse = False
        if pulse_port:
            start_pulse = True

        start_autoland = False
        if autoland_port:
            start_autoland = True
            start_hgrb = True

        start_rbweb = False
        if rbweb_port or start_autoland or start_hgrb:
            start_rbweb = True
            start_ldap = True

        known_images = self.all_docker_images()
        if db_image and db_image not in known_images:
            db_image = None
        if web_image and web_image not in known_images:
            web_image = None
        if hgrb_image and hgrb_image not in known_images:
            hgrb_image = None
        if ldap_image and ldap_image not in known_images:
            ldap_image = None
        if pulse_image and pulse_image not in known_images:
            pulse_image = None
        if autoland_image and autoland_image not in known_images:
            autoland_image = None
        if autolanddb_image and autolanddb_image not in known_images:
            autolanddb_image = None

        if (not db_image or not web_image or not hgrb_image or not ldap_image
                or not pulse_image or not autolanddb_image
                or not autoland_image or not rbweb_image):
            images = self.build_mozreview(verbose=verbose)
            autolanddb_image = images['autolanddb']
            autoland_image = images['autoland']
            db_image = images['bmodb']
            hgrb_image = images['hgrb']
            ldap_image = images['ldap']
            web_image = images['bmoweb']
            pulse_image = images['pulse']
            rbweb_image = images['rbweb']

        containers = self.state['containers'].setdefault(cluster, [])

        with futures.ThreadPoolExecutor(5) as e:
            # Create containers concurrently - no race conditions here.
            f_db_create = e.submit(self.client.create_container, db_image,
                    environment={'MYSQL_ROOT_PASSWORD': 'password'})
            if start_pulse:
                f_pulse_create = e.submit(self.client.create_container,
                        pulse_image)

            bmo_url = 'http://%s:%s/' % (self.docker_hostname, http_port)

            f_web_create = e.submit(self.client.create_container,
                    web_image, environment={'BMO_URL': bmo_url})

            if start_rbweb:
                f_rbweb_create = e.submit(self.client.create_container,
                                          rbweb_image,
                                          command=['/run'],
                                          entrypoint=['/entrypoint.py'],
                                          ports=[80])

            if start_ldap:
                f_ldap_create = e.submit(self.client.create_container,
                                         ldap_image)

            if start_hgrb:
                f_hgrb_create = e.submit(self.client.create_container,
                                         hgrb_image,
                                         command=['/run.sh'],
                                         entrypoint=['/entrypoint.py'],
                                         ports=[22, 80])

            if start_autoland:
                f_autolanddb_create = e.submit(self.client.create_container,
                        autolanddb_image)

                f_autoland_create = e.submit(self.client.create_container,
                        autoland_image)

            # We expose the database to containers. Start it first.
            db_id = f_db_create.result()['Id']
            containers.append(db_id)
            f_db_start = e.submit(self.client.start, db_id)

            if start_autoland:
                autolanddb_id = f_autolanddb_create.result()['Id']
                containers.append(autolanddb_id)
                f_start_autolanddb = e.submit(self.client.start, autolanddb_id)

            # RabbitMQ takes a while to start up. Start it before other
            # containers. (We probably could have a callback-driven mechanism
            # here to ensure no time is lost. But that is more complex.)
            if start_pulse:
                pulse_id = f_pulse_create.result()['Id']
                containers.append(pulse_id)
                f_start_pulse = e.submit(self.client.start, pulse_id,
                                         port_bindings={5672: pulse_port})

            if start_ldap:
                ldap_id = f_ldap_create.result()['Id']
                containers.append(ldap_id)
                f_start_ldap = e.submit(self.client.start, ldap_id,
                                        port_bindings={389: ldap_port})

            f_db_start.result()
            db_state = self.client.inspect_container(db_id)

            web_id = f_web_create.result()['Id']
            containers.append(web_id)

            if start_autoland:
                f_start_autolanddb.result()
                autolanddb_state = self.client.inspect_container(autolanddb_id)
                autoland_id = f_autoland_create.result()['Id']
                containers.append(autoland_id)
                autoland_state = self.client.inspect_container(autoland_id)

            if start_hgrb:
                hgrb_id = f_hgrb_create.result()['Id']
                containers.append(hgrb_id)

            if start_rbweb:
                rbweb_id = f_rbweb_create.result()['Id']
                containers.append(rbweb_id)

            # At this point, all containers have been created.
            self.save_state()

            f_start_web = e.submit(self.client.start, web_id,
                    links=[(db_state['Name'], 'bmodb')],
                    port_bindings={80: http_port})
            f_start_web.result()
            web_state = self.client.inspect_container(web_id)

            if start_pulse:
                f_start_pulse.result()
                pulse_state = self.client.inspect_container(pulse_id)

            if start_ldap:
                f_start_ldap.result()
                ldap_state = self.client.inspect_container(ldap_id)

            if start_hgrb:
                self.client.start(hgrb_id,
                                  links=[(ldap_state['Name'], 'ldap')],
                                  port_bindings={22: ssh_port, 80: hg_port})
                hgrb_state = self.client.inspect_container(hgrb_id)

            if start_autoland:
                assert start_hgrb
                f_start_autoland = e.submit(self.client.start, autoland_id,
                        links=[(autolanddb_state['Name'], 'db'),
                               (web_state['Name'], 'bmoweb'),
                               (hgrb_state['Name'], 'hgrb')],
                        port_bindings={80: autoland_port})
                f_start_autoland.result()
                autoland_state = self.client.inspect_container(autoland_id)

            if start_rbweb:
                assert start_autoland
                self.client.start(rbweb_id,
                                  links=[(web_state['Name'], 'bmoweb'),
                                         (pulse_state['Name'], 'pulse'),
                                         (hgrb_state['Name'], 'hgrb'),
                                         (autoland_state['Name'], 'autoland'),
                                         (ldap_state['Name'], 'ldap')
                                  ],
                                  port_bindings={80: rbweb_port})
                rbweb_state = self.client.inspect_container(rbweb_id)

        bmoweb_hostname, bmoweb_hostport = \
                self._get_host_hostname_port(web_state, '80/tcp')
        bmo_url = 'http://%s:%d/' % (bmoweb_hostname, bmoweb_hostport)

        if start_pulse:
            rabbit_hostname, rabbit_hostport = \
                self._get_host_hostname_port(pulse_state, '5672/tcp')

        if start_hgrb:
            hgssh_hostname, hgssh_hostport = \
                self._get_host_hostname_port(hgrb_state, '22/tcp')
            hgweb_hostname, hgweb_hostport = \
                self._get_host_hostname_port(hgrb_state, '80/tcp')

        if start_rbweb:
            rbweb_hostname, rbweb_hostport = \
                self._get_host_hostname_port(rbweb_state, '80/tcp')
            rbweb_url = 'http://%s:%s/' % (rbweb_hostname, rbweb_hostport)

        print('waiting for Bugzilla to start')
        wait_for_http(bmoweb_hostname, bmoweb_hostport,
                      extra_check_fn=self._get_assert_container_running_fn(web_id))
        if start_pulse:
            wait_for_amqp(rabbit_hostname, rabbit_hostport, 'guest', 'guest',
                          extra_check_fn=self._get_assert_container_running_fn(pulse_id))
        if start_hgrb:
            wait_for_ssh(hgssh_hostname, hgssh_hostport,
                         extra_check_fn=self._get_assert_container_running_fn(hgrb_id))
            wait_for_http(hgweb_hostname, hgweb_hostport,
                          extra_check_fn=self._get_assert_container_running_fn(hgrb_id))
        if start_rbweb:
            wait_for_http(rbweb_hostname, rbweb_hostport,
                          extra_check_fn=self._get_assert_container_running_fn(rbweb_id))

        print('Bugzilla accessible on %s' % bmo_url)

        result = {
            'bugzilla_url': bmo_url,
            'db_id': db_id,
            'web_id': web_id,
        }

        if start_autoland:
            result['autolanddb_id'] = autolanddb_id
            result['autoland_id'] = autoland_id
            autoland_hostname, autoland_hostport = \
                    self._get_host_hostname_port(autoland_state, '80/tcp')
            result['autoland_url'] = 'http://%s:%d/' % (autoland_hostname,
                                                        autoland_hostport)

        if start_pulse:
            result['pulse_id'] = pulse_id
            result['pulse_host'] = rabbit_hostname
            result['pulse_port'] = rabbit_hostport

        if start_ldap:
            ldap_hostname, ldap_hostport = \
                    self._get_host_hostname_port(ldap_state, '389/tcp')
            result['ldap_id'] = ldap_id
            result['ldap_uri'] = 'ldap://%s:%d/' % (ldap_hostname,
                                                    ldap_hostport)

        if start_hgrb:
            result['hgrb_id'] = hgrb_id
            result['ssh_hostname'] = hgssh_hostname
            result['ssh_port'] = hgssh_hostport
            result['mercurial_url'] = 'http://%s:%d/' % (hgweb_hostname,
                                                         hgweb_hostport)

        if start_rbweb:
            result['rbweb_id'] = rbweb_id
            result['reviewboard_url'] = rbweb_url

        return result

    def stop_bmo(self, cluster):
        count = 0

        with futures.ThreadPoolExecutor(4) as e:
            for container in reversed(self.state['containers'].get(cluster, [])):
                count += 1
                e.submit(self.client.remove_container, container, force=True)

        print('stopped %d containers' % count)

        try:
            del self.state['containers'][cluster]
            self.save_state()
        except KeyError:
            pass

    def build_all_images(self, verbose=False, use_last=False):
        images = self.ensure_images_built([
            'autolanddb',
            'autoland',
            'bmodb-volatile',
            'bmoweb',
            'ldap',
            'pulse',
        ], ansibles={
            'hgmaster': ('docker-hgmaster', 'centos6'),
            'hgweb': ('docker-hgweb', 'centos6'),
            'hgrb': ('docker-hgrb', 'centos6'),
            'rbweb': ('docker-rbweb', 'centos6'),
        }, verbose=verbose, use_last=use_last)

        with futures.ThreadPoolExecutor(2) as e:
            f_mr = e.submit(self.build_mozreview, images=images,
                            verbose=verbose, use_last=use_last)
            f_hgmo = e.submit(self.build_hgmo, images=images, verbose=verbose,
                              use_last=use_last)

        self.prune_images()

        return f_mr.result(), f_hgmo.result()

    def _get_files_from_http_container(self, builder, message):
        image = self.ensure_built(builder, verbose=True)
        container = self.client.create_container(image)['Id']

        with self.start_container(container, port_bindings={80: None}) as state:
            port = int(state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])

            print(message)
            wait_for_http(self.docker_hostname, port, timeout=120,
                          extra_check_fn=self._get_assert_container_running_fn(container))

            res = requests.get('http://%s:%s/' % (self.docker_hostname, port))

            files = {}
            for filename, data in res.json().items():
                files[filename] = base64.b64decode(data)

        self.client.remove_container(container)

        return files

    def build_mercurial_rpms(self):
        return self._get_files_from_http_container('hgrpm',
            'Generating RPMs...')

    def get_full_image(self, image):
        for i in self.client.images():
            if i['Id'][0:12] == image:
                return i['Id']

        return image

    def prune_images(self):
        """Prune images that are old and likely unused."""
        running = set(self.get_full_image(c['Image'])
                      for c in self.client.containers())

        ignore_images = set([
            self.state['last-autoland-id'],
            self.state['last-autolanddb-id'],
            self.state['last-bmodb-id'],
            self.state['last-bmoweb-id'],
            self.state['last-hgrb-id'],
            self.state['last-pulse-id'],
            self.state['last-rbweb-id'],
            self.state['last-bmodb-bootstrap-id'],
            self.state['last-bmoweb-bootstrap-id'],
            self.state['last-hgmaster-id'],
            self.state['last-hgweb-id'],
            self.state['last-ldap-id'],
            self.state['last-vct-id'],
        ])

        relevant_repos = set([
            'bmoweb',
            'bmoweb-bootstrapped',
            'bmodb-volatile',
            'bmodb-volatile-bootstrapped',
            'pulse',
            'rbweb',
            'autolanddb',
            'autolanddb-bootstrapped',
            'autoland',
            'autoland-bootstrapped',
            'hgmaster',
            'hgrb',
            'hgweb',
            'ldap',
            'vct',
        ])

        to_delete = {}

        for i in self.client.images():
            iid = i['Id']

            # Don't do anything with images attached to running containers -
            # Docker won't allow it.
            if iid in running:
                continue

            # Don't do anything with our last used images.
            if iid in ignore_images:
                continue

            for repotag in i['RepoTags']:
                repo, tag = repotag.split(':')
                if repo in relevant_repos:
                    to_delete[iid] = repo
                    break

        retained = {}
        for key, image in sorted(self.state['images'].items()):
            if image not in to_delete:
                retained[key] = image

        with futures.ThreadPoolExecutor(8) as e:
            for image, repo in to_delete.items():
                print('Pruning old %s image %s' % (repo, image))
                e.submit(self.client.remove_image, image)

        self.state['images'] = retained
        self.save_state()

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh, indent=4, sort_keys=True)

    def all_docker_images(self):
        """Obtain the set of all known Docker image IDs."""
        return {i['Id'] for i in self.client.images(all=True)}

    @contextmanager
    def start_container(self, cid, **kwargs):
        """Context manager for starting and stopping a Docker container.

        The container with id ``cid`` will be started when the context manager is
        entered and stopped when the context manager is execited.

        The context manager receives the inspected state of the container,
        immediately after it is started.
        """
        self.client.start(cid, **kwargs)
        try:
            state = self.client.inspect_container(cid)
            yield state
        finally:
            try:
                self.client.stop(cid, timeout=20)
            except DockerAPIError as e:
                # Silently ignore failures if the container doesn't exist, as
                # the container is obviously stopped.
                if e.response.status_code != 404:
                    raise



    @contextmanager
    def create_container(self, image, remove_volumes=False, **kwargs):
        """Context manager for creating a temporary container.

        A container will be created from an image. When the context manager
        exists, the container will be removed.

        This context manager is useful for temporary containers that shouldn't
        outlive the life of the process.
        """
        s = self.client.create_container(image, **kwargs)
        try:
            yield s
        finally:
            self.client.remove_container(s['Id'], force=True, v=remove_volumes)

    @contextmanager
    def vct_container(self, image=None, cid=None, verbose=False):
        """Obtain a container with content of v-c-t available inside.

        We employ some hacks to make this as fast as possible. Three run modes
        are possible:

        1) Client passes in a running container (``cid``)
        2) A previously executed container is available to start
        3) We create and start a temporary container.

        The multiple code paths make the logic a bit difficult. But it makes
        code in consumers slightly easier to follow.
        """
        existing_cid = self.state['vct-cid']

        # If we're going to use an existing container, verify it exists.
        if not cid and existing_cid:
            try:
                state = self.client.inspect_container(existing_cid)
            except DockerAPIError:
                existing_cid = None
                self.state['vct-cid'] = None

        # Build the image if we're in temporary container mode.
        if not image and not cid and not existing_cid:
            image = self.ensure_built('vct', verbose=verbose)

        start = False

        if cid:
            state = self.client.inspect_container(cid)
            if not state['State']['Running']:
                raise Exception('Passed container ID is not running')
        elif existing_cid:
            cid = existing_cid
            start = True
        else:
            cid = self.client.create_container(image,
                                               volumes=['/vct-mount'],
                                               ports=[873])['Id']
            start = True

        try:
            if start:
                self.client.start(cid, port_bindings={873: None})
                state = self.client.inspect_container(cid)
                port = state['NetworkSettings']['Ports']['873/tcp'][0]['HostPort']
                url = 'rsync://%s:%s/vct-mount/' % (self.docker_hostname, port)

                get_and_write_vct_node()
                vct_paths = self._get_vct_files()
                with tempfile.NamedTemporaryFile() as fh:
                    for f in sorted(vct_paths.keys()):
                        fh.write('%s\n' % f)
                    fh.write('.vctnode\n')
                    fh.flush()

                    rsync('-a', '--delete-before', '--files-from', fh.name, ROOT, url)

                self.state['last-vct-id'] = image
                self.state['vct-cid'] = cid
                self.save_state()

            yield state
        finally:
            if start:
                self.client.stop(cid)

    @contextmanager
    def auto_clean_orphans(self):
        if not self.is_alive():
            yield
            return

        containers = {c['Id'] for c in self.client.containers(all=True)}
        images = {i['Id'] for i in self.client.images(all=True)}
        try:
            yield
        finally:
            with futures.ThreadPoolExecutor(8) as e:
                for c in self.client.containers(all=True):
                    if c['Id'] not in containers:
                        e.submit(self.client.remove_container, c['Id'],
                                 force=True)

            with futures.ThreadPoolExecutor(8) as e:
                for i in self.client.images(all=True):
                    if i['Id'] not in images:
                        e.submit(self.client.remove_image, c['Id'])

    def get_file_content(self, cid, path):
        """Get the contents of a file from a container."""
        r = self.client.copy(cid, path)
        buf = BytesIO(r.read())
        buf.seek(0)
        t = tarfile.open(mode='r', fileobj=buf)
        fp = t.extractfile(os.path.basename(path))
        return fp.read()

    def get_directory_contents(self, cid, path, tar='/bin/tar'):
        """Obtain the contents of all files in a directory in a container.

        This is done by invoking "tar" inside the container and piping the
        results to us.

        This returns an iterable of ``tarfile.TarInfo``, fileobj 2-tuples.
        """
        data = self.client.execute(cid, [tar, '-c', '-C', path, '-f', '-', '.'],
                                   stderr=False)
        buf = BytesIO(data)
        t = tarfile.open(mode='r', fileobj=buf)
        for member in t:
            f = t.extractfile(member)
            member.name = member.name[2:]
            yield member, f

    def get_code_coverage(self, cid, filemap=None):
        """Obtain code coverage data from a container.

        Containers can be programmed to collect code coverage from executed
        programs automatically. Our convention is to place coverage files in
        ``/coverage``.

        This method will fetch coverage files and parse them into data
        structures, which it will emit.

        If a ``filemap`` dict is passed, it will be used to map filenames
        inside the container to local filesystem paths. When present,
        files not inside the map will be ignored.
        """
        filemap = filemap or {}

        for member, fh in self.get_directory_contents(cid, '/coverage'):
            if not member.name.startswith('coverage.'):
                continue

            data = pickle.load(fh)

            c = CoverageData(basename=member.name,
                             collector=data.get('collector'))

            lines = {}
            for f, linenos in data.get('lines', {}).items():
                newname = filemap.get(f)
                if not newname:
                    # Ignore entries missing from map.
                    if filemap:
                        continue

                    newname = f

                lines[newname] = dict.fromkeys(linenos, None)

            arcs = {}
            for f, arcpairs in data.get('arcs', {}).items():
                newname = filemap.get(f)
                if not newname:
                    if filemap:
                        continue

                    newname = f

                arcs[newname] = dict.fromkeys(arcpairs, None)

            if not lines and not arcs:
                continue

            c.lines = lines
            c.arcs = arcs

            yield c

    def _get_host_hostname_port(self, state, port):
        """Resolve the host hostname and port number for an exposed port."""
        host_port = state['NetworkSettings']['Ports'][port][0]
        host_ip = host_port['HostIp']
        host_port = int(host_port['HostPort'])

        if host_ip != '0.0.0.0':
            return host_ip, host_port

        if self.docker_hostname != 'localhost':
            return self.docker_hostname, host_port

        # This works when Docker is running locally, which is common. But it
        # is far from robust.
        gateway = state['NetworkSettings']['Gateway']
        return gateway, host_port

    def _get_assert_container_running_fn(self, cid):
        """Obtain a function that raises during invocation if a container stops."""
        def assert_running():
            try:
                info = self.client.inspect_container(cid)
            except DockerAPIError as e:
                if e.response.status_code == 404:
                    raise Exception('Container does not exist '
                                    '(stopped running?): %s' % cid)

                raise

            if not info['State']['Running']:
                raise Exception('Container stopped running: %s' % cid)

        return assert_running
