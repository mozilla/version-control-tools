# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is used to manage Docker containers in the context of running
# Mercurial tests.

from __future__ import absolute_import, print_function

import docker
import json
import os
import pickle
import requests
import ssl
import subprocess
import sys
import tarfile
import warnings

# TRACKING py3
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from docker.errors import (
    DockerException,
)
from contextlib import contextmanager
from io import BytesIO

from coverage.data import CoverageData


HERE = os.path.abspath(os.path.dirname(__file__))
DOCKER_DIR = os.path.normpath(os.path.join(HERE, "..", "docker"))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def rsync(*args):
    prog = None
    for path in os.environ["PATH"].split(":"):
        candidate = os.path.join(path, "rsync")
        if os.path.exists(candidate):
            prog = candidate
            break

    if not prog:
        raise Exception("Could not find rsync program")

    subprocess.check_call([prog] + list(args), cwd="/")


class DockerNotAvailable(Exception):
    """Error raised when Docker is not available."""


def params_from_env(env):
    """Obtain Docker connect parameters from the environment.

    This returns a tuple that should be used for base_url and tls arguments
    of Docker.__init__.
    """
    host = env.get("DOCKER_HOST", None)
    tls = False

    if env.get("DOCKER_TLS_VERIFY"):
        tls = True

    # This is likely encountered with boot2docker.
    cert_path = env.get("DOCKER_CERT_PATH")
    if cert_path:
        ca_path = os.path.join(cert_path, "ca.pem")
        tls_cert_path = os.path.join(cert_path, "cert.pem")
        tls_key_path = os.path.join(cert_path, "key.pem")

        # Hostnames will attempt to be verified by default. We don't know what
        # the hostname should be, so don't attempt it.
        tls = docker.tls.TLSConfig(
            client_cert=(tls_cert_path, tls_key_path),
            ssl_version=ssl.PROTOCOL_TLSv1,
            ca_cert=ca_path,
            verify=True,
            assert_hostname=False,
        )

    # docker-py expects the protocol to have something TLS in it. tcp:// won't
    # work. Hack around it until docker-py works as expected.
    if tls and host:
        if host.startswith("tcp://"):
            host = host.replace("tcp://", "https://")

    return host, tls


@contextmanager
def docker_rollback_on_error(client):
    """Perform Docker operations as a transaction of sorts.

    Returns a modified Docker client instance. Creation events performed
    on the client while the context manager is active will be undone if
    an exception occurs. This allows complex operations such as the creation
    of multiple containers to be rolled back automatically if an error
    occurs.
    """
    created_containers = set()
    created_networks = set()

    class ProxiedDockerClient(client.__class__):
        def create_container(self, *args, **kwargs):
            res = super(ProxiedDockerClient, self).create_container(*args, **kwargs)
            created_containers.add(res["Id"])
            return res

        def create_network(self, *args, **kwargs):
            res = super(ProxiedDockerClient, self).create_network(*args, **kwargs)
            created_networks.add(res["Id"])
            return res

    old_class = client.__class__
    try:
        client.__class__ = ProxiedDockerClient
        yield client
    except Exception:
        for cid in created_containers:
            client.remove_container(cid, v=True, force=True)
        for nid in created_networks:
            client.remove_network(nid)
        raise
    finally:
        client.__class__ = old_class


class Docker(object):
    def __init__(self, url, tls=False):
        self._ddir = DOCKER_DIR
        self.state = {
            "clobber-hgweb": None,
            "clobber-hgmaster": None,
            "clobber-hgrb": None,
            "clobber-rbweb": None,
            "images": {},
            "containers": {},
            "last-pulse-id": None,
            "last-rbweb-id": None,
            "last-rbweb-bootstrap-id": None,
            "last-hgrb-id": None,
            "last-hgmaster-id": None,
            "last-hgweb-id": None,
            "last-ldap-id": None,
            "last-vct-id": None,
            "last-treestatus-id": None,
            "vct-cid": None,
        }

        keys = (
            "clobber-hgweb",
            "clobber-hgmaster",
            "clobber-hgrb",
            "clobber-rbweb",
            "last-pulse-id",
            "last-rbweb-id",
            "last-rbweb-bootstrap-id",
            "last-hgmaster-id",
            "last-hgrb-id",
            "last-hgweb-id",
            "last-ldap-id",
            "last-vct-id",
            "last-treestatus-id",
            "vct-cid",
        )
        for k in keys:
            self.state.setdefault(k, None)

        try:
            self.client = docker.DockerClient(base_url=url, tls=tls, version="auto")
            self.api_client = self.client.api
        except DockerException:
            self.client = None
            self.api_client = None
            return

        # We need API 1.22+ for some networking APIs.
        if docker.utils.compare_version("1.22", self.api_client.api_version) < 0:
            warnings.warn(
                "Warning: unable to speak to Docker servers older than Docker 1.10.x"
            )
            self.client = None
            self.api_client = None
            return

        # Try to obtain a network hostname for the Docker server. We use this
        # for determining where to look for opened ports.
        # This is a bit complicated because Docker can be running from a local
        # socket or or another host via something like boot2docker.

        # This is wrong - the gateway returned is the _internal_ IP gateway for
        # running containers.  docker makes no guarantee it will be routable
        # from the host; and on MacOS this is indeed not routable.  Port mapping
        # and querying for the HostIP should be used instead (or use a sane
        # docker build system such as docker-compose).

        docker_url = urlparse.urlparse(self.api_client.base_url)
        self.docker_hostname = docker_url.hostname
        if docker_url.hostname in ("localunixsocket", "localhost", "127.0.0.1"):
            networks = self.api_client.networks()
            for network in networks:
                if network["Name"] == "bridge":
                    ipam = network["IPAM"]
                    try:
                        addr = ipam["Config"][0]["Gateway"]
                    except KeyError:
                        warnings.warn(
                            "Warning: Unable to determine ip "
                            "address of the docker gateway. Please "
                            "ensure docker is listening on a tcp "
                            "socket by setting -H "
                            "tcp://127.0.0.1:4243 in your docker "
                            "configuration file."
                        )
                        self.client = None
                        self.api_client = None
                        break

                    self.docker_hostname = addr
                    break

    def is_alive(self):
        """Whether the connection to Docker is alive."""
        if not self.client:
            return False

        # This is a layering violation with docker.client, but meh.
        try:
            self.api_client._get(self.api_client._url("/version"), timeout=5)
            return True
        except requests.exceptions.RequestException:
            return False

    def network_config(self, network_name, alias):
        """Obtain a networking config object."""
        return self.api_client.create_networking_config(
            endpoints_config={
                network_name: self.api_client.create_endpoint_config(
                    aliases=[alias],
                )
            }
        )

    @contextmanager
    def auto_clean_orphans(self, runtests_label):
        """Ensure all containers with the special `runtests_label` are cleaned."""
        if not runtests_label or not self.is_alive():
            yield
            return

        try:
            yield
        finally:
            # Get all containers with a matching shutdown label
            try:
                filters = {
                    "label": f"hgcluster.run-tests={runtests_label}",
                }
                orphan_containers = self.client.containers.list(
                    filters=filters,
                )
                orphan_networks = self.client.networks.list(
                    filters=filters,
                )
            except docker.errors.APIError as err:
                print(
                    "Failed to retrieve networks and containers for cleanup.",
                    file=sys.stderr,
                )
                print(err, file=sys.stderr)
                return

            # Remove leftover containers
            success, failure = 0, 0
            for container in orphan_containers:
                try:
                    container.remove(force=True, v=True)
                    success += 1
                except docker.errors.APIError as err:
                    print(
                        f"Failed to cleanup container: {str(container)}",
                        file=sys.stderr,
                    )
                    print(err, file=sys.stderr)
                    failure += 1
            print(
                f"Finished cleaning {success} containers"
                f"{f' ({failure} failed)' if failure else ''}."
            )

            success, failure = 0, 0
            for network in orphan_networks:
                try:
                    network.remove()
                    success += 1
                except docker.errors.APIError as err:
                    print(
                        f"Failed to cleanup network: {str(network)}.", file=sys.stderr
                    )
                    print(err, file=sys.stderr)
                    failure += 1
            print(
                f"Finished cleaning {success} networks"
                f"{f' ({failure} failed)' if failure else ''}."
            )

    def execute(self, cid, cmd, stdout=False, stderr=False, stream=False, detach=False):
        """Execute a command on a container.

        Returns the output of the command.

        This mimics the old docker.execute() API, which was removed in
        docker-py 1.3.0.
        """
        r = self.api_client.exec_create(cid, cmd, stdout=stdout, stderr=stderr)
        return self.api_client.exec_start(r["Id"], stream=stream, detach=detach).decode(
            "utf-8"
        )

    def get_file_content(self, cid, path):
        """Get the contents of a file from a container."""
        r, stat = self.api_client.get_archive(cid, path)
        buf = BytesIO()
        for chunk in r:
            buf.write(chunk)
        buf.seek(0)
        t = tarfile.open(mode="r", fileobj=buf)
        fp = t.extractfile(os.path.basename(path))
        return fp.read()

    def get_directory_contents(self, cid, path, tar="/bin/tar"):
        """Obtain the contents of all files in a directory in a container.

        This is done by invoking "tar" inside the container and piping the
        results to us.

        This returns an iterable of ``tarfile.TarInfo``, fileobj 2-tuples.
        """
        data = self.execute(
            cid, [tar, "-c", "-C", path, "-f", "-", "."], stdout=True, stderr=False
        )
        buf = BytesIO(data)
        t = tarfile.open(mode="r", fileobj=buf)
        for member in t:
            f = t.extractfile(member)
            member.name = member.name[2:]
            yield member, f

    def get_code_coverage(self, cid, filemap=None):
        """Obtain code coverage data from a container.

        Containers can be programmed to collect code coverage from executed
        programs automatically. Our convention is to place coverage files in
        ``/coverage``.

        This method will fetch coverage files and parse them into data
        structures, which it will emit.

        If a ``filemap`` dict is passed, it will be used to map filenames
        inside the container to local filesystem paths. When present,
        files not inside the map will be ignored.
        """
        filemap = filemap or {}

        for member, fh in self.get_directory_contents(cid, "/coverage"):
            if not member.name.startswith("coverage."):
                continue

            data = pickle.load(fh)

            c = CoverageData(basename=member.name, collector=data.get("collector"))

            lines = {}
            for f, linenos in data.get("lines", {}).items():
                newname = filemap.get(f)
                if not newname:
                    # Ignore entries missing from map.
                    if filemap:
                        continue

                    newname = f

                lines[newname] = dict.fromkeys(linenos, None)

            arcs = {}
            for f, arcpairs in data.get("arcs", {}).items():
                newname = filemap.get(f)
                if not newname:
                    if filemap:
                        continue

                    newname = f

                arcs[newname] = dict.fromkeys(arcpairs, None)

            if not lines and not arcs:
                continue

            c.lines = lines
            c.arcs = arcs

            yield c

    def _get_host_hostname_port(self, state, port):
        """Resolve the host hostname and port number for an exposed port."""
        host_port = state["NetworkSettings"]["Ports"][port][0]
        host_ip = host_port["HostIp"]
        host_port = int(host_port["HostPort"])

        if host_ip != "0.0.0.0":
            return host_ip, host_port

        if self.docker_hostname not in ("localhost", "127.0.0.1"):
            return self.docker_hostname, host_port

        for network in state["NetworkSettings"]["Networks"].values():
            if network["Gateway"]:
                return network["Gateway"], host_port

        # This works when Docker is running locally, which is common. But it
        # is far from robust.
        gateway = state["NetworkSettings"]["Gateway"]
        return gateway, host_port
