#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

import docker
import json
import os
import socket
import sys
import time
import urlparse

HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.join(HERE, 'docker')

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

    def ensure_built(self, name):
        """Ensure a Docker image from a builder directory is built."""
        p = os.path.join(self._ddir, 'builder-%s' % name)
        if not os.path.isdir(p):
            raise Exception('Unknown Docker builder name: %s' % name)

        image = self.state['images'].get(name)
        if image:
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
                image = image.rstrip()
                break

        self.state['images'][name] = image

        return image

    def ensure_bmo_built(self):
        """Ensure the images for a BMO service are built."""
        db_image = self.ensure_built('bmodb')
        web_image = self.ensure_built('bmoweb')

        return db_image, web_image

    def start_bmo(self, http_port):
        """Start a BMO service accepting HTTP traffic on the specified port."""
        db_image, web_image = self.ensure_bmo_built()

        # We assume the hostname running Docker is the hostname we'll
        # expose BMO as.
        hostname = urlparse.urlparse(self.client.base_url).hostname
        url = 'http://%s:%s/' % (hostname, http_port)

        db_id = self.state['containers'].get('bmodb')
        if not db_id:
            db_id = self.client.create_container(db_image,
                    environment={'MYSQL_ROOT_PASSWORD': 'password'})['Id']
            self.state['containers']['bmodb'] = db_id

        web_id = self.state['containers'].get('bmoweb')
        if not web_id:

            r = self.client.create_container(web_image,
                    environment={'BMO_URL': url})
            web_id = r['Id']
            self.state['containers']['bmoweb'] = web_id

        db_state = self.client.inspect_container(db_id)
        web_state = self.client.inspect_container(web_id)

        if not db_state['State']['Running']:
            self.client.start(db_id)
            db_state = self.client.inspect_container(db_id)

        if not web_state['State']['Running']:
            self.client.start(web_id,
                    links=[(db_state['Name'], 'bmodb')],
                    port_bindings={80: http_port})
            web_state = self.client.inspect_container(web_id)

        print('waiting for Bugzilla HTTP server to start')
        sys.stdout.flush()
        wait_for_socket(hostname, http_port)
        print('Bugzilla web server listening at %s' % url)

    def stop_bmo(self):
        db_id = self.state['containers'].get('bmodb')
        web_id = self.state['containers'].get('bmoweb')

        if web_id:
            self.client.stop(web_id)
            self.client.remove_container(web_id)
            del self.state['containers']['bmoweb']
        if db_id:
            self.client.stop(db_id)
            self.client.remove_container(db_id)
            del self.state['containers']['bmodb']

    def save_state(self):
        with open(self._state_path, 'wb') as fh:
            json.dump(self.state, fh)

def main(args):
    if 'DOCKER_STATE_FILE' not in os.environ:
        print('DOCKER_STATE_FILE must be defined')
        return 1

    docker_url = os.environ.get('DOCKER_HOST', None)

    d = Docker(os.environ['DOCKER_STATE_FILE'], docker_url)

    action = args[0]

    if action == 'build-bmo':
        d.ensure_bmo_built()
    elif action == 'start-bmo':
        d.start_bmo(args[1])
    elif action == 'stop-bmo':
        d.stop_bmo()

    d.save_state()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
