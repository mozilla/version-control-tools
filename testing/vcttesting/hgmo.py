# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import errno
import json
import os
import subprocess
import sys
import uuid

import concurrent.futures as futures

from .ldap import LDAP
from .util import (
    docker_compose_down_background,
    get_available_port,
    normalize_testname,
    wait_for_amqp,
    wait_for_kafka,
    wait_for_kafka_topic,
    wait_for_ssh,
)

import yaml

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
HGCLUSTER_DOCKER_COMPOSE = os.path.join(ROOT, 'testing', 'hgcluster-docker-compose.yml')


class HgCluster(object):
    """Interface to a cluster of HG servers.

    This class manages Docker contains and environments that replicate the
    hg.mozilla.org server configuration.
    """
    MASTER_FILE_MAP = {
        'hgext/pushlog/feed.py': '/var/hg/version-control-tools/hgext/pushlog/feed.py',
        'hgext/pushlog/__init__.py': '/var/hg/version-control-tools/hgext/pushlog/__init__.py',
        'hgext/serverlog/__init__.py': '/var/hg/version-control-tools/hgext/serverlog/__init__.py',
        'hgserver/pash/pash.py': '/usr/local/bin/pash.py',
        'hgserver/pash/hg_helper.py': '/usr/local/bin/hg_helper.py',
        'hgserver/hgmolib/hgmolib/ldap_helper.py': '/usr/local/bin/ldap_helper.py',
        'hgserver/pash/repo_group.py': '/usr/local/bin/repo_group.py',
        'hgserver/pash/sh_helper.py': '/usr/local/bin/sh_helper.py',
    }

    def __init__(self, docker):
        self._d = docker
        self.testname = normalize_testname(os.getenv('TESTNAME'))

        with open(HGCLUSTER_DOCKER_COMPOSE) as f:
            self.docker_compose_content = yaml.safe_load(f)

        if not self.testname:
            print('$TESTNAME environment variable not set - commands will fail without '
                  'specifying a cluster name.')

    def get_cluster_containers(self, onetime=False):
        '''Return containers corresponding to the cluster with the specified name.
        '''
        import time

        initial = time.time()
        while True:
            project_containers = self._d.client.containers.list(
                # Use sparse to avoid inspecting each container for information. Also
                # avoids a race condition when attempting to inspect a container that no
                # longer exists, resulting in a stack trace.
                sparse=True,
                filters={
                    'label': 'com.docker.compose.project=%s' % self.testname
                }
            )

            if onetime:
                break

            # Wait until ports are properly exposed
            if len(project_containers) == len(self.docker_compose_content['services']):
                break

            if time.time() - initial > 60:
                raise Exception("timeout reached waiting for all 5 containers")

        # Call `reload` to acquire data about our sparsely acquired objects
        for container in project_containers:
            container.reload()

        return {
            container.labels['com.docker.compose.service']: container
            for container in project_containers
        }

    def get_state(self):
        '''Return a dict containing variables to be exported into the test environment shell.
        '''
        containers = self.get_cluster_containers()

        params = {}

        params['pulse_hostname'], params['pulse_hostport'] = self._d._get_host_hostname_port(
            containers['pulse'].attrs, '5672/tcp'
        )
        params['master_ssh_hostname'], params['master_ssh_port'] = self._d._get_host_hostname_port(
            containers['hgssh'].attrs, '22/tcp'
        )
        _, _, params['master_host_ed25519_key'], params['master_host_rsa_key'] = self.get_mirror_ssh_keys(
            containers['hgssh'].id
        )
        params['ldap_uri'] = 'ldap://%s:%s' % self._d._get_host_hostname_port(containers['ldap'].attrs, '389/tcp')
        params['master_id'] = containers['hgssh'].id
        params['hgweb_0_url'] = 'http://%s:%s/' % self._d._get_host_hostname_port(containers['hgweb0'].attrs, '80/tcp')
        params['hgweb_1_url'] = 'http://%s:%s/' % self._d._get_host_hostname_port(containers['hgweb1'].attrs, '80/tcp')
        params['hgweb_0_cid'] = containers['hgweb0'].id
        params['hgweb_1_cid'] = containers['hgweb1'].id
        params['kafka_0_hostport'] = '%s:%s' % self._d._get_host_hostname_port(containers['hgssh'].attrs, '9092/tcp')
        params['kafka_1_hostport'] = '%s:%s' % self._d._get_host_hostname_port(containers['hgweb0'].attrs, '9092/tcp')
        params['kafka_2_hostport'] = '%s:%s' % self._d._get_host_hostname_port(containers['hgweb1'].attrs, '9092/tcp')

        return params

    @staticmethod
    def build(image=None):
        """Build the hgcluster images."""
        docker_compose_build_command = [
            'docker-compose',
            # Use the `hgcluster-docker-compose` file
            '--file', HGCLUSTER_DOCKER_COMPOSE,
            'build',
            '--parallel',
            # Specify which images to avoid building hgweb twice
            'hgweb0',
            'hgssh',
            'pulse',
            'ldap',
        ]

        if image:
            docker_compose_build_command.append(image)

        subprocess.run(
            docker_compose_build_command,
            check=True,
        )

    def start(self, master_ssh_port=None, show_output=False):
        """Start the cluster.

        If ``coverage`` is True, code coverage for Python executions will be
        obtained.
        """
        if not self.testname:
            raise Exception('cluster name is not set')

        if self.get_cluster_containers(onetime=True):
            raise Exception('pre-existing containers exist for project %s;\n'
                            '(try running `hgmo clean` or `docker container rm`)' % self.testname)

        # docker-compose needs the arguments in this order
        docker_compose_up_command = [
            'docker-compose',
            # Use the `hgcluster-docker-compose` file
            '--file', HGCLUSTER_DOCKER_COMPOSE,
            # Specify the project name for cluster management via container labels
            '--project-name', self.testname,
            'up',
            # Always recreate containers and volumes
            '--force-recreate',
            '--renew-anon-volumes',
            # Use detached mode to run containers in the background
            '-d',
        ]

        newenv = os.environ.copy()

        if master_ssh_port:
            # Use a `:` here, so that leaving the field blank will cause it to be
            # empty in the docker-compose file, allowing us to `docker-compose down`
            # without knowing the master ssh port of the cluster.
            newenv['MASTER_SSH_PORT'] = '%d:' % master_ssh_port

        kwargs = {'env': newenv}
        if not show_output:
            # TRACKING py3 - once we have full Py3 support in the test environment
            # we can make use of `subprocess.DEVNULL`
            devnull = open(os.devnull, 'wb')
            kwargs['stderr'] = devnull
            kwargs['stdout'] = devnull

        compose_up_process = subprocess.Popen(docker_compose_up_command, **kwargs)

        try:
            cluster_containers = self.get_cluster_containers()
        except Exception as e:
            print(e, file=sys.stderr)
            print('\n', file=sys.stderr)

            return_code = compose_up_process.wait()

            print('docker-compose errored with exit code %d: stderr:\n%s' %
                  (return_code, compose_up_process.stderr),
                  file=sys.stderr)
            sys.exit(1)

        all_states = {
            name: state
            for name, state in cluster_containers.items()
            if 'hg' in name
        }
        web_states = {
            name: state
            for name, state in all_states.items()
            if 'hgweb' in name
        }

        # Number of hg related containers, and number of web heads
        n_web = len(web_states)
        n_hg = len(all_states)

        # Fail early here so we aren't surprised if `network_name` is an unexpected value
        if not all(len(state.attrs['NetworkSettings']['Networks']) == 1 for state in all_states.values()):
            raise Exception('Each container should only have one network attached')

        network_name = list(
            cluster_containers['hgssh'].attrs['NetworkSettings']['Networks'].keys()
        )[0]

        master_id = cluster_containers['hgssh'].id
        web_ids = [state.id for state in web_states.values()]

        # Obtain replication and host SSH keys.
        mirror_private_key, mirror_public_key, master_host_ed25519_key, master_host_rsa_key = \
            self.get_mirror_ssh_keys(master_id)

        with futures.ThreadPoolExecutor(n_web) as e:
            # Set SSH keys on hgweb instances.
            cmd = [
                '/set-mirror-key.py',
                mirror_private_key,
                mirror_public_key,
                'hgssh',
                # FUTURE this will need updated once hgweb supports ed25519 keys
                master_host_rsa_key,
            ]
            for i in web_ids:
                e.submit(self._d.execute, i, cmd)

        # The host SSH keys are populated during container start as part of
        # entrypoint.py. There is a race between the keys being generated and
        # us fetching them. We wait on a network service (Kafka) started in
        # entrypoint.py after SSH keys are generated to eliminate this race
        # condition.
        futures_list = []
        with futures.ThreadPoolExecutor(n_web) as e:
            for name, state in web_states.items():
                # Wait until we can access Kafka from the host machine
                host, port = self._d._get_host_hostname_port(state.attrs, '9092/tcp')
                futures_list.append(e.submit(wait_for_kafka, '%s:%s' % (host, port), 180))

        for f in futures_list:
            f.result()

        f_mirror_host_keys = []
        with futures.ThreadPoolExecutor(n_web) as e:
            # Obtain host keys from mirrors.
            for state in web_states.values():
                f_mirror_host_keys.append((
                    state.attrs['NetworkSettings']['Networks'][network_name]['IPAddress'],
                    e.submit(self._d.get_file_content, state.id,
                             '/etc/ssh/ssh_host_rsa_key.pub')))

        # Tell the master about all the mirrors.
        args = ['/set-mirrors.py']
        for ip, f_key in f_mirror_host_keys:
            key = (
                f_key
                .result()
                .decode('utf-8')
                .strip()
            )
            key = ' '.join(key.split()[0:2])
            args.extend([ip, key])
        self._d.execute(master_id, args)

        master_ssh_hostname, master_ssh_hostport = \
                self._d._get_host_hostname_port(cluster_containers['hgssh'].attrs, '22/tcp')
        pulse_hostname, pulse_hostport = \
                self._d._get_host_hostname_port(cluster_containers['pulse'].attrs, '5672/tcp')

        futures_list = []
        # 4 threads, one for each service we need to wait on
        with futures.ThreadPoolExecutor(4) as e:
            futures_list.append(e.submit(self.ldap.create_vcs_sync_login,
                               mirror_public_key))
            futures_list.append(e.submit(wait_for_amqp, pulse_hostname,
                               pulse_hostport, 'guest', 'guest'))
            futures_list.append(e.submit(wait_for_ssh, master_ssh_hostname,
                               master_ssh_hostport))
            # We already waited on the web nodes above. So only need to
            # wait on master here.
            h, p = self._d._get_host_hostname_port(cluster_containers['hgssh'].attrs, '9092/tcp')
            futures_list.append(e.submit(wait_for_kafka, '%s:%s' % (h, p), 20))

        # Will re-raise exceptions.
        for f in futures_list:
            f.result()

        # Create Kafka topics.
        TOPICS = [
            ('pushdata', '8'),
            ('replicatedpushdatapending', '1'),
            ('replicatedpushdata', '1'),
        ]
        futures_list = []
        with futures.ThreadPoolExecutor(len(TOPICS)) as e:
            for topic, partitions in TOPICS:
                cmd = [
                    '/opt/kafka/bin/kafka-topics.sh',
                    '--create',
                    '--topic', topic,
                    '--partitions', partitions,
                    '--replication-factor', str(n_hg),
                    '--config', 'min.insync.replicas=2',
                    '--config', 'unclean.leader.election.enable=false',
                    '--config', 'max.message.bytes=104857600',
                    '--zookeeper', 'hgssh:2181/hgmoreplication,hgweb0:2181/hgmoreplication,hgweb1:2181/hgmoreplication',
                ]
                futures_list.append(e.submit(self._d.execute, master_id, cmd,
                                   stdout=True))

        for f in futures.as_completed(futures_list):
            result = f.result()
            if 'Created topic' not in result:
                raise Exception('kafka topic not created: %s' % result)

        # There appears to be a race condition between the topic being
        # created and the topic being available. So we explicitly wait
        # for the topic to appear on all clients so processes within
        # containers don't need to wait.
        with futures.ThreadPoolExecutor(4) as e:
            futures_list = []
            for state in all_states.values():
                h, p = self._d._get_host_hostname_port(state.attrs, '9092/tcp')
                hostport = '%s:%s' % (h, p)
                for topic in TOPICS:
                    futures_list.append(e.submit(wait_for_kafka_topic, hostport,
                                       topic[0]))

            [f.result() for f in futures_list]

        return self.get_state()

    def clean(self, cluster_name=None, show_output=False):
        """Clean the cluster.

        Containers will be shut down and removed. The state file will
        destroyed.
        """
        cluster_name = normalize_testname(cluster_name or self.testname)
        docker_compose_down_background(cluster_name, show_output=show_output)

    @property
    def ldap(self):
        state = self.get_state()
        return LDAP(state['ldap_uri'], 'cn=admin,dc=mozilla', 'password')

    def get_mirror_ssh_keys(self, master_id=None):
        with futures.ThreadPoolExecutor(4) as e:
            f_private_key = e.submit(self._d.get_file_content, master_id,
                                     '/etc/mercurial/mirror')
            f_public_key = e.submit(self._d.get_file_content, master_id,
                                    '/etc/mercurial/mirror.pub')
            f_host_ed25519_key = e.submit(self._d.get_file_content, master_id,
                                          '/etc/mercurial/ssh/ssh_host_ed25519_key.pub')
            f_host_rsa_key = e.submit(self._d.get_file_content, master_id,
                                      '/etc/mercurial/ssh/ssh_host_rsa_key.pub')

        host_ed25519_key = ' '.join(
            f_host_ed25519_key
            .result()
            .decode('utf-8')
            .split()[0:2]
        )
        host_rsa_key = ' '.join(
            f_host_rsa_key
            .result()
            .decode('utf-8')
            .split()[0:2]
        )

        return (
            f_private_key.result().decode('utf-8'),
            f_public_key.result().decode('utf-8'),
            host_ed25519_key,
            host_rsa_key,
        )
            

    def create_repo(self, name, group='scm_level_1'):
        """Create a repository on the cluster.

        ``path`` is the path fragment the repository would be accessed under
        at https://hg.mozilla.org. e.g. ``hgcustom/version-control-tools``.

        The repository will be owned by the specified ``group``.
        """
        cmd = ['/create-repo', name, group]

        state = self.get_state()

        return self._d.execute(state['master_id'], cmd, stdout=True, stderr=True)

    def aggregate_code_coverage(self, destdir):
        master_map = {}
        for host, container in self.MASTER_FILE_MAP.items():
            master_map[container] = os.path.join(ROOT, host)

        for c in self._d.get_code_coverage(self.master_id, filemap=master_map):
            dest = os.path.join(destdir, 'coverage.%s' % uuid.uuid1())
            c.write_file(dest)
