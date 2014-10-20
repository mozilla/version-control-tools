# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

from __future__ import absolute_import

import docker
import json
import os
import requests
import socket
import subprocess
import sys
import tarfile
import time
import urlparse
import uuid
from io import BytesIO

HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, '..', 'docker'))

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
                ca_cert=ca_path, verify=True, assert_hostname=False)

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
            'last-db-bootstrap-id': None,
            'last-web-bootstrap-id': None,
        }

        if os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                self.state = json.load(fh)

        self.state.setdefault('last-db-id', None)
        self.state.setdefault('last-web-id', None)
        self.state.setdefault('last-db-bootstrap-id', None)
        self.state.setdefault('last-web-bootstrap-id', None)

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

    def ensure_built(self, name, verbose=False):
        """Ensure a Docker image from a builder directory is built and up to date"""
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

    def build_bmo(self, verbose=False):
        """Ensure the images for a BMO service are built.

        bmoweb's entrypoint does a lot of setup on first run. This takes many
        seconds to perform and this cost is unacceptable for efficient test
        running. So, when we build the BMO images, we create throwaway
        containers and commit the results to a new image. This allows us to
        spin up multiple bmoweb containers very quickly.
        """
        images = self.state['images']
        db_image = self.ensure_built('bmodb-volatile', verbose=verbose)
        web_image = self.ensure_built('bmoweb', verbose=verbose)

        self.state['last-db-id'] = db_image
        self.state['last-web-id'] = web_image

        # The keys for the bootstrapped images are derived from the base
        # images they depend on. This means that if we regenerate a new
        # base image, the bootstrapped images will be regenerated.
        db_bootstrapped_key = 'bmodb-bootstrapped:%s' % db_image
        web_bootstrapped_key = 'bmoweb-bootstrapped:%s:%s' % (
                db_image, web_image)

        have_db = db_bootstrapped_key in images
        have_web = web_bootstrapped_key in images

        if have_db and have_web:
            return images[db_bootstrapped_key], images[web_bootstrapped_key]

        db_id = self.client.create_container(db_image,
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']

        web_environ = {}
        # Temporarily pin Bugzilla commit until bootstrapping is fixed.
        # See bug 1074586.
        web_environ['BMO_COMMIT'] = '1f84551e1414eeba886e04e0e9e2a8e61d568fc1'

        if 'FETCH_BMO' in os.environ:
            web_environ['FETCH_BMO'] = '1'

        web_id = self.client.create_container(web_image,
                environment=web_environ)['Id']

        self.client.start(db_id)
        db_state = self.client.inspect_container(db_id)

        self.client.start(web_id,
                links=[(db_state['Name'], 'bmodb')],
                port_bindings={80: None})
        web_state = self.client.inspect_container(web_id)

        http_port = int(web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
        print('waiting for bmoweb to bootstrap')
        wait_for_http(self.docker_hostname, http_port)

        # Ask the containers to shut down gracefully.
        # This gives the MySQL container opportunity to flush, etc.
        self.client.stop(web_id, timeout=20)
        self.client.stop(db_id, timeout=20)

        db_unique_id = str(uuid.uuid1())
        web_unique_id = str(uuid.uuid1())

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
        self.state['images'][db_bootstrapped_key] = db_bootstrap
        self.state['images'][web_bootstrapped_key] = web_bootstrap
        self.state['last-db-bootstrap-id'] = db_bootstrap
        self.state['last-web-bootstrap-id'] = web_bootstrap
        self.save_state()

        self.client.remove_container(web_id)
        self.client.remove_container(db_id)

        print('Bootstrapped BMO images created')

        return db_bootstrap, web_bootstrap

    def start_bmo(self, cluster, hostname=None, http_port=80, db_image=None,
            web_image=None):
        if not db_image or not web_image:
            db_image, web_image = self.build_bmo()

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
        self.save_state()

        self.client.start(db_id)
        db_state = self.client.inspect_container(db_id)
        self.client.start(web_id,
                links=[(db_state['Name'], 'bmodb')],
                port_bindings={80: http_port})
        web_state = self.client.inspect_container(web_id)

        print('waiting for Bugzilla to start')
        wait_for_http(self.docker_hostname, http_port)
        print('Bugzilla accessible on %s' % url)

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
            self.state['last-db-bootstrap-id'],
            self.state['last-web-bootstrap-id'],
        ])

        relevant_repos = set([
            'bmoweb',
            'bmoweb-bootstrapped',
            'bmodb-volatile',
            'bmodb-volatile-bootstrapped',
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
