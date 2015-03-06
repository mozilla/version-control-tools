# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os
import signal
import socket
import time

import kombu
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


def kill(pid):
    os.kill(pid, signal.SIGINT)

    while psutil.pid_exists(pid):
        time.sleep(0.1)
