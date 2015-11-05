# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import socket
import subprocess
import time

from kafka.client import KafkaClient
import kombu
import paramiko
import requests


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def get_available_port():
    """Obtain a port number available for binding."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    host, port = s.getsockname()
    s.close()

    return port


def wait_for_http(host, port, path='', timeout=240, extra_check_fn=None):
    """Wait for an HTTP server to respond.

    If extra_check_fn is defined, it will be called as an extra check to see if
    we should still poll. If we should not (e.g. the underlying container
    stopped running), that function should raise an exception.
    """

    start = time.time()

    while True:
        try:
            requests.get('http://%s:%s/%s' % (host, port, path), timeout=1)
            return
        except requests.exceptions.RequestException:
            pass

        if extra_check_fn:
            extra_check_fn()

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for HTTP')

        time.sleep(0.1)


def wait_for_amqp(hostname, port, userid, password, ssl=False, timeout=60,
                  extra_check_fn=None):
    c = kombu.Connection(hostname=hostname, port=port, userid=userid,
            password=password, ssl=ssl)

    start = time.time()

    while True:
        try:
            c.connection
            return
        except Exception:
            pass

        if extra_check_fn:
            extra_check_fn()

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for AMQP')

        time.sleep(0.1)


class IgnoreHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return


def wait_for_ssh(hostname, port, timeout=60, extra_check_fn=None):
    """Wait for an SSH server to start on the specified host and port."""
    start = time.time()

    while True:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(IgnoreHostKeyPolicy())
        try:
            client.connect(hostname, port=port, timeout=0.1, allow_agent=False,
                           look_for_keys=False)
            client.close()
            return
        except socket.error:
            pass
        except paramiko.SSHException:
            # This is probably wrong. We should ideally attempt authentication
            # and wait for an explicit auth failed instead of a generic
            # error.
            return

        if extra_check_fn:
            extra_check_fn()

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for SSH')

        time.sleep(0.1)


def wait_for_kafka(hostport, timeout=60):
    """Wait for Kafka to start responding on the specified host:port string."""
    start = time.time()
    while True:
        try:
            KafkaClient(hostport, client_id=b'dummy', timeout=1)
            return
        except Exception:
            pass

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for Kafka')

        time.sleep(0.1)


def get_and_write_vct_node():
    hg = os.path.join(ROOT, 'venv', 'bin', 'hg')
    env = dict(os.environ)
    env['HGRCPATH'] = '/dev/null'
    args = [hg, '-R', ROOT, 'log', '-r', '.', '-T', '{node|short}']
    with open(os.devnull, 'wb') as null:
        node = subprocess.check_output(args, env=env, cwd='/', stderr=null)

    with open(os.path.join(ROOT, '.vctnode'), 'wb') as fh:
        fh.write(node)

    return node
