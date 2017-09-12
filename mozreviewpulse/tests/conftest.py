# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os

import kombu as kombu
import pytest
import docker as docker_py
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry

from mozreviewpulse.testing import MountebankClient, run_container, \
    run_mountebank_server


def wait_for_connection(url, retries=5):
    """Helper to retry a HTTP request."""
    s = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(total=retries, backoff_factor=0.1))
    s.mount('http://', adapter)
    s.get(url)


@pytest.fixture(scope='session')
def docker():
    client = docker_py.APIClient(os.environ.get('DOCKER_HOST', None))

    # client readiness check
    try:
        client.info()
    except requests.ConnectionError as e:
        pytest.skip("Error connecting to docker daemon: {0}".format(e))

    return client


@pytest.fixture(scope='session')
def mountebank_server(request, docker):
    """Run a mountebank service container in Docker."""
    mb_host_info = run_mountebank_server(request, docker, record_requests=True)
    mb_url = 'http://{0}:{1}'.format(mb_host_info.ip, mb_host_info.adminport)
    wait_for_connection(mb_url)
    return mb_host_info


@pytest.fixture(scope='function')
def mountebank(request, mountebank_server):
    client = MountebankClient(
        mountebank_server.ip,
        mountebank_server.adminport,
        mountebank_server.imposterport)

    request.addfinalizer(client.reset_imposters)

    if request.cls:
        # We are being used as a fixture for a unittest.TestCase.
        request.cls.mountebank = client
        request.cls.mountebank_host_info = mountebank_server
    return client


@pytest.fixture(scope='function')
def pulse_server(request, docker):
    """Run a Mozilla Pulse service container in Docker."""
    # Use 'rabbitmq:3-management' so that the management plugin is installed
    # and enabled. See https://hub.docker.com/_/rabbitmq/
    ip = run_container(request, docker, 'rabbitmq:3-management')
    return ip


@pytest.fixture
def pulse_conn(request, pulse_server):
    conn = kombu.Connection(pulse_server, port=5672)
    request.addfinalizer(conn.release)
    # Wait for the service to come up
    conn.ensure_connection(
        max_retries=10, interval_start=0.3, interval_step=0.3)
    return conn


@pytest.fixture
def pulse_producer(pulse_conn):
    exchange = kombu.Exchange('exchange/mrp/', type='topic')
    producer = kombu.Producer(pulse_conn, exchange=exchange)

    # Ensure the exchange is declared so that consumers
    # can start listening before a message is published.
    producer.maybe_declare(producer.exchange)
    return producer
