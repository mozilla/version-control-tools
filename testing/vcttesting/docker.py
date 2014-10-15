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

class Docker(object):
    def __init__(self, state_path, url):
        self._ddir = DOCKER_DIR
        self._state_path = state_path
        self.state = {
            'images': {},
            'containers': {},
        }

        if os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                self.state = json.load(fh)

        self.client = docker.Client(base_url=url)

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
                tag=name, stream=True):
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
                return self.get_full_image(image.rstrip())

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
        """Prune images belonging to old revisions we no longer care about."""
        running = set(self.get_full_image(c['Image'])
                      for c in self.client.containers())

        existing = set(i['Id'] for i in self.client.images())
        retained = {}
        for key, image in sorted(self.state['images'].items()):
            if image not in existing:
                continue

            if image in running:
                retained[key] = image
            else:
                print('Removing image %s (%s)' % (image, key))
                self.client.remove_image(image)

        self.state['images'] = retained
        self.save_state()

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh)
