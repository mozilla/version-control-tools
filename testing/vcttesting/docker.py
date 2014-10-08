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
import time
import urlparse

HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, '..', 'docker'))

def wait_for_socket(host, port, timeout=60):
    """Wait for a TCP socket to accept connections."""

    start = time.time()

    while True:
        try:
            socket.create_connection((host, port), timeout=1)
            return
        except socket.error:
            pass

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for socket')

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

        # We use the Mercurial working copy node to track images.
        # We assume the current working directory is inside a Mercurial
        # repository.
        env = dict(os.environ)
        env['HGRCPATH'] = '/dev/null'
        cmd = ['hg', 'identify', '-i']

        # We may not be executed from the working directory of a
        # version-control-tools checkout. Try harder to find it.
        if 'TESTDIR' in env:
            cmd.extend(['-R', env['TESTDIR']])
        node = subprocess.check_output(cmd, shell=True, env=env)
        self._hgnode = node.strip()
        self._hgdirty = '+' in node

    def is_alive(self):
        """Whether the connection to Docker is alive."""
        # This is a layering violation with docker.client, but meh.
        try:
            self.client._get(self.client._url('/version'), timeout=1)
            return True
        except requests.exceptions.RequestException:
            return False

    def ensure_built(self, name):
        """Ensure a Docker image from a builder directory is built and up to date"""
        p = os.path.join(self._ddir, 'builder-%s' % name)
        if not os.path.isdir(p):
            raise Exception('Unknown Docker builder name: %s' % name)

        # Image is derived from the working copy. If dirty, always rebuild
        # because all bets are off.
        key = '%s:%s' % (name, self._hgnode)
        image = self.state['images'].get(key)
        if image and not self._hgdirty:
            return image

        # TODO create a lock to avoid race conditions.

        # The API here is wonky, possibly due to buggy behavior in
        # docker.client always setting stream=True if version > 1.8.
        # We assume this is a bug that will change behavior later and work
        # around it by ensuring consisten behavior.
        print('Building Docker image %s' % name)
        for stream in self.client.build(path=p, stream=True):
            s = json.loads(stream)
            if 'stream' not in s:
                continue

            s = s['stream']
            #sys.stdout.write(s)
            if s.startswith('Successfully built '):
                image = s[len('Successfully built '):]
                # There is likely a trailing newline.
                image = self.get_full_image(image.rstrip())
                break

        self.state['images'][key] = image
        self.save_state()

        return image

    def build_bmo(self):
        """Ensure the images for a BMO service are built.

        bmoweb's entrypoint does a lot of setup on first run. This takes many
        seconds to perform and this cost is unacceptable for efficient test
        running. So, when we build the BMO images, we create throwaway
        containers and commit the results to a new image. This allows us to
        spin up multiple bmoweb containers very quickly.
        """
        images = self.state['images']
        db_image = self.ensure_built('bmodb-volatile')
        web_image = self.ensure_built('bmoweb')

        # The keys for the bootstrapped images are derived from the base
        # images they depend on. This means that if we regenerate a new
        # base image, the bootstrapped images will be regenerated.
        db_bootstrapped_key = 'bmodb-bootstrapped:%s:%s' % (
                self._hgnode, db_image)
        web_bootstrapped_key = 'bmoweb-bootstrapped:%s:%s:%s' % (
                self._hgnode, db_image, web_image)

        have_db = db_bootstrapped_key in images
        have_web = web_bootstrapped_key in images

        if have_db and have_web and not self._hgdirty:
            return images[db_bootstrapped_key], images[web_bootstrapped_key]

        # If we already have the bootstrapped image, just throw it away
        # and recreate it. This catches the case where we have a dirty working
        # copy.
        if db_bootstrapped_key in images:
            self.client.remove_image(images[db_bootstrapped_key])
        if web_bootstrapped_key in images:
            self.client.remove_image(images[web_bootstrapped_key])

        # should fix that.
        db_id = self.client.create_container(db_image,
                environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']

        web_id = self.client.create_container(web_image)['Id']

        self.client.start(db_id)
        db_state = self.client.inspect_container(db_id)

        self.client.start(web_id,
                links=[(db_state['Name'], 'bmodb')],
                port_bindings={80: None})
        web_state = self.client.inspect_container(web_id)

        http_port = int(web_state['NetworkSettings']['Ports']['80/tcp'][0]['HostPort'])
        print('waiting for bmoweb to bootstrap')
        wait_for_socket(self.docker_hostname, http_port)

        db_bootstrap = self.client.commit(db_id)['Id']
        web_bootstrap = self.client.commit(web_id)['Id']
        self.state['images'][db_bootstrapped_key] = db_bootstrap
        self.state['images'][web_bootstrapped_key] = web_bootstrap
        self.save_state()

        self.client.kill(web_id)
        self.client.kill(db_id)
        db_state = self.client.inspect_container(db_id)
        web_state = self.client.inspect_container(web_id)

        if web_state['State']['Running']:
            self.client.stop(web_id)
        if db_state['State']['Running']:
            self.client.stop(db_id)

        self.client.remove_container(web_id)
        self.client.remove_container(db_id)

        return db_bootstrap, web_bootstrap

    def start_bmo(self, cluster, hostname=None, http_port=80):
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
        wait_for_socket(self.docker_hostname, http_port)
        print('Bugzilla accessible on %s' % url)

    def stop_bmo(self, cluster):
        count = 0
        for container in self.state['containers'].get(cluster, []):
            count += 1
            self.client.kill(container)
            self.client.stop(container)
            info = self.client.inspect_container(container)
            self.client.remove_container(container)

            image = info['Image']
            if image not in self.state['images'].values():
                self.client.remove_image(info['Image'])

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

            if self._hgnode in key or image in running:
                retained[key] = image
            else:
                print('Removing image %s (%s)' % (image, key))
                self.client.remove_image(image)

        self.state['images'] = retained
        self.save_state()

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh)
