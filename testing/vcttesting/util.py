# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import signal
import socket
import time

import kombu
import paramiko
import psutil
import requests


def get_available_port():
    """Obtain a port number available for binding."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    host, port = s.getsockname()
    s.close()

    return port


def wait_for_http(host, port, path='', timeout=60):
    """Wait for an HTTP response."""

    start = time.time()

    while True:
        try:
            requests.get('http://%s:%s/%s' % (host, port, path), timeout=1)
            return
        except requests.exceptions.RequestException:
            pass

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for HTTP')

        time.sleep(0.1)


def wait_for_amqp(hostname, port, userid, password, ssl=False, timeout=60):
    c = kombu.Connection(hostname=hostname, port=port, userid=userid,
            password=password, ssl=ssl)

    start = time.time()

    while True:
        try:
            c.connection
            return
        except Exception:
            pass

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for AMQP')

        time.sleep(0.1)


class IgnoreHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return


def wait_for_ssh(hostname, port, timeout=60):
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

        if time.time() - start > timeout:
            raise Exception('Timeout reached waiting for SSH')

        time.sleep(0.1)


def kill(pid):
    os.kill(pid, signal.SIGINT)

    while psutil.pid_exists(pid):
        time.sleep(0.1)
