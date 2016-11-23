# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test helpers.
"""
import json
from collections import namedtuple

import requests


class MountebankClient:

    def __init__(self, host, port=2525, imposter_port=4000):
        self.host = host
        self.port = port
        self.imposter_port = imposter_port

    @property
    def imposters_admin_url(self):
        return self.get_endpoint_with_port(self.port, '/imposters')

    @property
    def stub_baseurl(self):
        return self.get_endpoint_with_port(self.imposter_port)

    def get_endpoint(self, path=''):
        """Construct a URL for the imposter service with optional path."""
        return self.get_endpoint_with_port(self.imposter_port, path)

    def get_endpoint_with_port(self, port, path=''):
        """Construct a service endpoint URL with port and optional path."""
        return 'http://{0}:{1}{2}'.format(self.host, port, path)

    def create_imposter(self, imposter_json):
        """Take a dict and turn it into a service stub."""
        response = requests.post(self.imposters_admin_url, json=imposter_json)
        if response.status_code != 201:
            raise RuntimeError(
                "mountebank imposter creation failed: {0} {1}".format(
                    response.status_code, response.content
                ))

    def create_stub(self, stub_json):
        """Create a single http stub using the default imposter port."""
        self.create_imposter({
            'port': self.imposter_port,
            'protocol': 'http',
            'stubs': [stub_json]
        })

    def reset_imposters(self):
        """Delete all imposters."""
        requests.delete(self.imposters_admin_url)

    def get_requests(self):
        """Return a list of requests made to the imposter."""
        url = self.imposters_admin_url + '/' + str(self.imposter_port)
        return requests.get(url).json().get('requests')


MBHostInfo = namedtuple('MBHostInfo', 'ip adminport imposterport')


def run_mountebank_server(request, docker_client, record_requests=False):
    """Run a mountebank service container in Docker."""

    # We do not record requests by default because it can cause a long-running
    # server to consume a lot of memory.
    # See http://www.mbtest.org/docs/api/mocks
    if record_requests:
        command = 'start --mock'
    else:
        command = 'start'

    ip = run_container(
        request,
        docker_client,
        'mountebank',
        # Sent to the mountebank server
        command=command,
        # The port our imposters will communicate over
        ports=[4000],
        # So mountebank process logs got to STDOUT and STDERR.
        tty=True
    )
    return MBHostInfo(ip, 2525, 4000)



def run_container(fixture_request, docker_client, image, cleanup=True, **kwargs):
    """Run and clean up a docker container."""
    host_config = docker_client.create_host_config(publish_all_ports=True)

    container = docker_client.create_container(
        image=image, host_config=host_config, **kwargs)
    docker_client.start(container=container["Id"])
    container_info = docker_client.inspect_container(container.get('Id'))

    ip = container_info["NetworkSettings"]["IPAddress"]

    def _cleanup():
        docker_client.remove_container(
            container=container["Id"],
            force=True
        )
    if cleanup:
        fixture_request.addfinalizer(_cleanup)

    return ip


def pull_image(docker_client, image_name, tag, **kwargs):
    """Pull or update a docker image."""
    response = docker_client.pull(image_name, tag=tag, **kwargs)
    # Grab the last line of output
    lastline = response.splitlines().pop()
    try:
        result = json.loads(lastline)
    except ValueError as e:
        raise Exception("Bad JSON result from docker pull: {0}".format(lastline))

    # Should get a dict of {'status': ...} on success and {'error': ...} on
    # failure.
    if 'error' in result:
        raise Exception("Failed to pull image: {0}".format(lastline))

    return image_name