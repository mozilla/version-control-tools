# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

from __future__ import absolute_import

import base64
import docker
import json
import os
import requests
import socket
import ssl
import subprocess
import sys
import tarfile
import time
import urlparse
import uuid
from contextlib import contextmanager
from io import BytesIO

HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, '..', 'docker'))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))

def wait_for_http(host, port, timeout=60):
    """Wait for an HTTP response."""

    start = time.time()

    while True:
        try:
            requests.get('http://%s:%s/' % (host, port), timeout=1)
            return
        except requests.exceptions.RequestException:
            pass

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for HTTP')

        time.sleep(1)


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
            'images': {},
            'containers': {},
            'last-db-id': None,
            'last-web-id': None,
            'last-rbweb-id': None,
            'last-db-bootstrap-id': None,
            'last-web-bootstrap-id': None,
            'last-rbweb-bootstrap-id': None,
        }

        if os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                self.state = json.load(fh)

        self.state.setdefault('last-db-id', None)
        self.state.setdefault('last-web-id', None)
        self.state.setdefault('last-rbweb-id', None)
        self.state.setdefault('last-db-bootstrap-id', None)
        self.state.setdefault('last-web-bootstrap-id', None)
        self.state.setdefault('last-rbweb-bootstrap-id', None)

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
            self.client._get(self.client._url('/version'), timeout=1)
            return True
        except requests.exceptions.RequestException:
            return False

    def ensure_built(self, name, verbose=False, add_vct=False):
        """Ensure a Docker image from a builder directory is built and up to date.

        This function is docker build++. Under the hood, it talks to the same
        ``build`` Docker API. However, it does one important thing differently:
        it builds the context archive manually.

        We supplement all contexts with the content of the source in this
        repository related to building Docker containers. If ``add_vct`` is
        True, we add the entire source repository to the Docker context.

        This added content can be ``ADD``ed to the produced image inside the
        Dockerfile. If the content changes, the Docker image ID changes and the
        cache is invalidated. This effectively allows downstream consumers to
        call ``ensure_built()`` as there *is the image up to date* check.
        """

        p = os.path.join(self._ddir, 'builder-%s' % name)
        if not os.path.isdir(p):
            raise Exception('Unknown Docker builder name: %s' % name)

        # TODO create a lock to avoid race conditions.

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

        # Include extra context from us and other support tools used for
        # creating [bootstrapped] images so Dockerfiles can ADD these files and
        # force cache invalidation of produced images if our logic changes.

        # Add ourself.
        tar.add(os.path.join(HERE, 'docker.py'), 'extra/vcttesting/docker.py')

        # Add the script for managing docker. This shouldn't be needed, but you
        # never know.
        tar.add(os.path.join(HERE, '..', 'docker-control.py'),
                'extra/docker-control.py')

        if add_vct:
            # We grab the set of tracked files in this repository.
            hg = os.path.join(ROOT, 'venv', 'bin', 'hg')
            env = dict(os.environ)
            env['HGRCPATH'] = '/dev/null'
            args = [hg, '-R', ROOT, 'locate', '-r', '.']
            output = subprocess.check_output(args, env=env, cwd='/')
            # And add them to the archive.
            for line in output.splitlines():
                filename = line.strip()
                tar.add(os.path.join(ROOT, filename), 'extra/vct/%s' % filename)

        tar.close()

        # Need to seek to beginning so .read() inside docker.client will return
        # data.
        buf.seek(0)

        # The API here is wonky, possibly due to buggy behavior in
        # docker.client always setting stream=True if version > 1.8.
        # We assume this is a bug that will change behavior later and work
        # around it by ensuring consistent behavior.
        print('Building Docker image %s' % name)
        for stream in self.client.build(fileobj=buf, custom_context=True,
                rm=True, stream=True):
            s = json.loads(stream)
            if 'stream' not in s:
                continue

            s = s['stream']
            if verbose:
                # s has newlines, so don't go through print().
                sys.stdout.write(s)
            if s.startswith('Successfully built '):
                image = s[len('Successfully built '):]
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

    def build_hgmo(self, verbose=False):
        """Ensure the images for a hg.mozilla.org service are built.

        hg-master runs the ssh service while hg-slave runs hgweb. The mirroring
        and other bits should be the same as in production with the caveat that
        LDAP integration is probably out of scope.
        """
        images = self.state['images']
        hg_master_image = self.ensure_built('hgmaster', add_vct=True, verbose=verbose)
        # hg_slave_image = self.ensure_built('hgslave', verbose=verbose)
        self.state['last-hgmaster-id'] = hg_master_image
        # self.state['last-hgslave-id'] = hg_slave_image

    def build_mozreview(self, verbose=False):
        """Ensure the images for a MozReview service are built.

        bmoweb's entrypoint does a lot of setup on first run. This takes many
        seconds to perform and this cost is unacceptable for efficient test
        running. So, when we build the BMO images, we create throwaway
        containers and commit the results to a new image. This allows us to
        spin up multiple bmoweb containers very quickly.
        """
        images = self.state['images']
        db_image = self.ensure_built('bmodb-volatile', verbose=verbose)
        web_image = self.ensure_built('bmoweb', verbose=verbose)
        #rbweb_image = self.ensure_built('rbweb', verbose=verbose, add_vct=True)

        self.state['last-db-id'] = db_image
        self.state['last-web-id'] = web_image
        #self.state['last-rbweb-id'] = rbweb_image

        # The keys for the bootstrapped images are derived from the base
        # images they depend on. This means that if we regenerate a new
        # base image, the bootstrapped images will be regenerated.
        db_bootstrapped_key = 'bmodb-bootstrapped:%s' % db_image
        web_bootstrapped_key = 'bmoweb-bootstrapped:%s:%s' % (
                db_image, web_image)
        #rbweb_bootstrapped_key = 'rbweb-bootstrapped:%s:%s' % (db_image,
        #        rbweb_image)

        have_db = db_bootstrapped_key in images
        have_web = web_bootstrapped_key in images
        #have_rbweb = rbweb_bootstrapped_key in images

        if have_db and have_web: # and have_rbweb:
            return (
                images[db_bootstrapped_key],
                images[web_bootstrapped_key],
                #images[rbweb_bootstrapped_key]
            )

        db_id = self.client.create_container(db_image,
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']

        web_environ = {}

        if 'FETCH_BMO' in os.environ:
            web_environ['FETCH_BMO'] = '1'

        web_id = self.client.create_container(web_image,
                environment=web_environ)['Id']
        #rbweb_id = self.client.create_container(rbweb_image)['Id']

        with self._start_container(db_id) as db_state:
            web_params = {
                'links': [(db_state['Name'], 'bmodb')],
                'port_bindings': {80: None},
            }
            rbweb_params = {
                'links': [(db_state['Name'], 'rbdb')],
                'port_bindings': {80: None},
            }
            with self._start_container(web_id, **web_params) as web_state:
                #with self._start_container(rbweb_id, **rbweb_params) as rbweb_state:
                bmoweb_port = int(web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
                #rbweb_port = int(rbweb_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
                print('waiting for containers to bootstrap')
                wait_for_http(self.docker_hostname, bmoweb_port)
                #wait_for_http(self.docker_hostname, rbweb_port)

        db_unique_id = str(uuid.uuid1())
        web_unique_id = str(uuid.uuid1())
        #rbweb_unique_id = str(uuid.uuid1())

        print('committing bootstrapped images')

        # Save an image of the stopped containers.
        # We tag with a unique ID so we can identify all bootrapped images
        # easily from Docker's own metadata. We have to give a tag becaue
        # Docker will forget the repository name if a name image has only a
        # repository name as well.
        db_bootstrap = self.client.commit(db_id,
                repository='bmodb-volatile-bootstrapped',
                tag=db_unique_id)['Id']
        web_bootstrap = self.client.commit(web_id,
                repository='bmoweb-bootstrapped',
                tag=web_unique_id)['Id']
        #rbweb_bootstrap = self.client.commit(rbweb_id,
        #        repository='rbweb-bootstrapped',
        #        tag=rbweb_unique_id)['Id']
        self.state['images'][db_bootstrapped_key] = db_bootstrap
        self.state['images'][web_bootstrapped_key] = web_bootstrap
        #self.state['images'][rbweb_bootstrapped_key] = rbweb_bootstrap
        self.state['last-db-bootstrap-id'] = db_bootstrap
        self.state['last-web-bootstrap-id'] = web_bootstrap
        #self.state['last-rbweb-bootstrap-id'] = rbweb_bootstrap
        self.save_state()

        print('removing non-bootstrapped containers')
        #self.client.remove_container(rbweb_id)
        self.client.remove_container(web_id)
        self.client.remove_container(db_id)

        print('bootstrapped images created')

        return db_bootstrap, web_bootstrap #, rbweb_bootstrap

    def start_mozreview(self, cluster, hostname=None, http_port=80,
            rbweb_port=None, db_image=None,
            web_image=None, rbweb_image=None, verbose=False):
        if not db_image or not web_image:
            db_image, web_image = self.build_mozreview(verbose=verbose)

        containers = self.state['containers'].setdefault(cluster, [])

        if not hostname:
            hostname = self.docker_hostname
        url = 'http://%s:%s/' % (hostname, http_port)

        db_id = self.client.create_container(db_image,
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']
        containers.append(db_id)
        web_id = self.client.create_container(web_image,
                environment={'BMO_URL': url})['Id']
        containers.append(web_id)
        #rbweb_id = self.client.create_container(rbweb_image)['Id']
        #containers.append(rbweb_id)
        self.save_state()

        self.client.start(db_id)
        db_state = self.client.inspect_container(db_id)
        self.client.start(web_id,
                links=[(db_state['Name'], 'bmodb')],
                port_bindings={80: http_port})
        web_state = self.client.inspect_container(web_id)
        #self.client.start(rbweb_id,
        #        links=[
        #            (db_state['Name'], 'rbdb'),
        #            (web_state['Name'], 'bzweb'),
        #        ],
        #        port_bindings={80: rbweb_port})
        #rbweb_state = self.client.inspect_container(rbweb_id)

        wait_bmoweb_port = web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        #wait_rbweb_port = rbweb_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']

        #rb_url = 'http://%s:%s/' % (hostname, wait_rbweb_port)

        print('waiting for Bugzilla to start')
        wait_for_http(self.docker_hostname, wait_bmoweb_port)
        #wait_for_http(self.docker_hostname, wait_rbweb_port)
        print('Bugzilla accessible on %s' % url)
        #print('Review Board accessible at %s' % rb_url)
        return url, db_id, web_id

    def stop_bmo(self, cluster):
        count = 0
        for container in reversed(self.state['containers'].get(cluster, [])):
            count += 1
            self.client.stop(container, timeout=10)
            self.client.remove_container(container)

            # The base image could be shared across multiple containers. So do
            # not try to delete it.

        print('stopped %d containers' % count)

        try:
            del self.state['containers'][cluster]
            self.save_state()
        except KeyError:
            pass

    def _get_files_from_http_container(self, builder, message):
        image = self.ensure_built(builder, verbose=True, add_vct=True)
        container = self.client.create_container(image)['Id']

        with self._start_container(container, port_bindings={80: None}) as state:
            port = int(state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])

            print(message)
            wait_for_http(self.docker_hostname, port, timeout=120)

            res = requests.get('http://%s:%s/' % (self.docker_hostname, port))

            files = {}
            for filename, data in res.json().items():
                files[filename] = base64.b64decode(data)

        self.client.remove_container(container)

        return files

    def build_reviewboard_eggs(self):
        return self._get_files_from_http_container('eggbuild',
            'Generating eggs...')

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

        candidates = []

        ignore_images = set([
            self.state['last-db-id'],
            self.state['last-web-id'],
            self.state['last-rbweb-id'],
            self.state['last-db-bootstrap-id'],
            self.state['last-web-bootstrap-id'],
            self.state['last-rbweb-bootstrap-id'],
        ])

        relevant_repos = set([
            'bmoweb',
            'bmoweb-bootstrapped',
            'bmodb-volatile',
            'bmodb-volatile-bootstrapped',
            'rbweb',
            'rbweb-bootstrapped',
        ])

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
                    candidates.append(iid)
                    break

        retained = {}
        for key, image in sorted(self.state['images'].items()):
            if image in candidates:
                retained[key] = image

        for iid in candidates:
            print('Removing image %s' % iid)
            self.client.remove_image(iid)

        self.state['images'] = retained
        self.save_state()

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh)

    @contextmanager
    def _start_container(self, cid, **kwargs):
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
            self.client.stop(cid, timeout=20)
