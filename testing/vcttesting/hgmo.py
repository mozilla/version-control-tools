# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import errno
import json
import os
import uuid

import concurrent.futures as futures

from .ldap import LDAP
from .util import (
    wait_for_amqp,
    wait_for_kafka,
    wait_for_kafka_topic,
    wait_for_ssh,
)


HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))


def get_hgweb_mozbuild_chroot(d):
    """Obtain files needed for a moz.build evaluation sandbox.

    Returns contents of binary files as a tuple. Files are:

    * tar.gz of chroot archive
    * executable for launching the moz.build evaluation process
    """
    image = d.ensure_built('hgweb-chroot', verbose=True)

    # The chroot archive contains a copy of version-control-tools. Need to
    # attach a vct container so we can rsync it over.
    with d.vct_container(verbose=True) as vct_state:
        host_config = d.api_client.create_host_config(
            volumes_from=[vct_state['Name']])
        with d.create_container(image, labels=['hgweb-chroot'],
                                host_config=host_config) as state:
            cid = state['Id']
            d.api_client.start(cid)

            for s in d.api_client.attach(cid, stream=True, logs=True):
                print(s, end='')

            tarball = d.get_file_content(state['Id'], '/chroot.tar.gz')
            executable = d.get_file_content(state['Id'], 'mozbuild-eval')

            return tarball, executable


class HgCluster(object):
    """Interface to a cluster of HG servers.

    This class manages Docker contains and environments that replicate the
    hg.mozilla.org server configuration.
    """
    MASTER_FILE_MAP = {
        'hgext/pushlog-legacy/pushlog-feed.py': '/var/hg/version-control-tools/hgext/pushlog-legacy/pushlog-feed.py',
        'hgext/pushlog/__init__.py': '/var/hg/version-control-tools/hgext/pushlog/__init__.py',
        'hgext/serverlog/__init__.py': '/var/hg/version-control-tools/hgext/serverlog/__init__.py',
        'hgserver/pash/pash.py': '/usr/local/bin/pash.py',
        'hgserver/pash/hg_helper.py': '/usr/local/bin/hg_helper.py',
        'hgserver/pash/ldap_helper.py': '/usr/local/bin/ldap_helper.py',
        'hgserver/pash/repo_group.py': '/usr/local/bin/repo_group.py',
        'hgserver/pash/sh_helper.py': '/usr/local/bin/sh_helper.py',
    }

    def __init__(self, docker, state_path=None, ldap_image=None,
                 master_image=None, web_image=None, pulse_image=None):
        self._d = docker
        self._dc = docker.api_client
        self.state_path = state_path

        if state_path and os.path.exists(state_path):
            with open(state_path, 'rb') as fh:
                state = json.load(fh)
                for k, v in state.items():
                    setattr(self, k, v)
        else:
            self.ldap_image = ldap_image
            self.master_image = master_image
            self.web_image = web_image
            self.pulse_image = pulse_image
            self.ldap_id = None
            self.master_id = None
            self.web_ids = []
            self.ldap_uri = None
            self.pulse_hostname = None
            self.pulse_hostport = None
            self.master_ssh_hostname = None
            self.master_ssh_port = None
            self.master_host_rsa_key = None
            self.master_host_ed25519_key = None
            self.web_urls = []
            self.kafka_hostports = []
            self.zookeeper_connect = None

    def start(self, ldap_port=None, master_ssh_port=None, web_count=2,
              pulse_port=None, coverage=False):
        """Start the cluster.

        If ``coverage`` is True, code coverage for Python executions will be
        obtained.
        """

        ldap_image = self.ldap_image
        master_image = self.master_image
        web_image = self.web_image
        pulse_image = self.pulse_image

        if not ldap_image or not master_image or not web_image or not pulse_image:
            images = self._d.build_hgmo(verbose=True)
            master_image = images['hgmaster']
            web_image = images['hgweb']
            ldap_image = images['ldap']
            pulse_image = images['pulse']

        zookeeper_id = 0

        network_name = 'hgmo-%s' % uuid.uuid4()
        self._dc.create_network(network_name, driver='bridge')

        def network_config(alias):
            return self._dc.create_networking_config(
                endpoints_config={
                    network_name: self._dc.create_endpoint_config(
                        aliases=[alias],
                    )
                }
            )

        with futures.ThreadPoolExecutor(5) as e:
            ldap_host_config = self._dc.create_host_config(
                port_bindings={389: ldap_port})
            f_ldap_create = e.submit(self._dc.create_container, ldap_image,
                                     labels=['ldap'],
                                     host_config=ldap_host_config,
                                     networking_config=network_config('ldap'))

            pulse_host_config = self._dc.create_host_config(
                port_bindings={5672: pulse_port})
            f_pulse_create = e.submit(self._dc.create_container, pulse_image,
                                      labels=['pulse'],
                                      host_config=pulse_host_config,
                                      networking_config=network_config('pulse'))

            env = {
                'ZOOKEEPER_ID': '%d' % zookeeper_id,
                'KAFKA_BROKER_ID': '%d' % zookeeper_id,
            }
            zookeeper_id += 1

            if coverage:
                env['CODE_COVERAGE'] = '1'

            master_host_config = self._dc.create_host_config(
                port_bindings={
                    22: master_ssh_port,
                    9092: None,
                },
            )

            f_master_create = e.submit(self._dc.create_container,
                master_image,
                environment=env,
                entrypoint=['/entrypoint.py'],
                command=['/usr/bin/supervisord', '-n'],
                ports=[22, 2181, 2888, 3888, 9092],
                host_config=master_host_config,
                labels=['hgssh'],
                networking_config=network_config('hgssh'))

            f_web_creates = []
            for i in range(web_count):
                env = {
                    'ZOOKEEPER_ID': '%d' % zookeeper_id,
                    'KAFKA_BROKER_ID': '%d' % zookeeper_id,
                }
                zookeeper_id += 1

                web_host_config = self._dc.create_host_config(
                    port_bindings={
                        22: None,
                        80: None,
                        9092: None,
                    },
                )

                f_web_creates.append(e.submit(self._dc.create_container,
                                              web_image,
                                              environment=env,
                                              ports=[22, 80, 2181, 2888, 3888, 9092],
                                              entrypoint=['/entrypoint.py'],
                                              command=['/usr/bin/supervisord', '-n'],
                                              host_config=web_host_config,
                                              labels=['hgweb', 'hgweb%d' % i],
                                              networking_config=network_config('hgweb%d' % i)))

            ldap_id = f_ldap_create.result()['Id']
            pulse_id = f_pulse_create.result()['Id']
            master_id = f_master_create.result()['Id']

            f_ldap_start = e.submit(self._dc.start, ldap_id)
            f_pulse_start = e.submit(self._dc.start, pulse_id)

            self._dc.start(master_id)
            master_state = self._dc.inspect_container(master_id)

            web_ids = [f.result()['Id'] for f in f_web_creates]
            fs = []
            for i in web_ids:
                fs.append(e.submit(self._dc.start, i))
            [f.result() for f in fs]

            f_web_states = []
            for i in web_ids:
                f_web_states.append(e.submit(self._dc.inspect_container, i))

            f_ldap_start.result()
            f_ldap_state = e.submit(self._dc.inspect_container, ldap_id)
            f_pulse_start.result()
            f_pulse_state = e.submit(self._dc.inspect_container, pulse_id)

            web_states = [f.result() for f in f_web_states]
            ldap_state = f_ldap_state.result()
            pulse_state = f_pulse_state.result()

        all_states = [master_state] + web_states

        # ZooKeeper and Kafka can't be started until the endpoints of nodes in
        # the cluster are known. The entrypoint script waits for a file created
        # by a process execution to come into existence before these daemons
        # are started. So do this early after startup.
        zk_ips = [s['NetworkSettings']['Networks'][network_name]['IPAddress']
                  for s in [master_state] + web_states]
        zookeeper_hostports = ['%s:2888:3888' % ip for ip in zk_ips]
        zookeeper_connect = ','.join('%s:2181/hgmoreplication' % ip for ip in zk_ips)
        web_hostnames = [s['Config']['Hostname'] for s in web_states]

        with futures.ThreadPoolExecutor(web_count + 1) as e:
            for s in all_states:
                command = [
                    '/set-kafka-servers',
                    s['NetworkSettings']['Networks'][network_name]['IPAddress'],
                    '9092',
                    ','.join(web_hostnames),
                ] + zookeeper_hostports
                e.submit(self._d.execute, s['Id'], command)

        # Obtain replication and host SSH keys.
        mirror_private_key, mirror_public_key, master_host_ed25519_key, master_host_rsa_key = \
            self.get_mirror_ssh_keys(master_id)

        with futures.ThreadPoolExecutor(web_count + 1) as e:
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

        # The host SSH keys are populated during container start. There
        # is a race between the keys being generated and us fetching them.
        # Wait on a daemon in the container to become available before
        # fetching host keys.
        fs = []
        with futures.ThreadPoolExecutor(web_count) as e:
            for s in web_states:
                h, p = self._d._get_host_hostname_port(s, '9092/tcp')
                fs.append(e.submit(wait_for_kafka, '%s:%s' % (h, p), 20))

        for f in fs:
            f.result()

        f_mirror_host_keys = []
        with futures.ThreadPoolExecutor(web_count) as e:
            # Obtain host keys from mirrors.
            for s in web_states:
                f_mirror_host_keys.append((
                    s['NetworkSettings']['Networks'][network_name]['IPAddress'],
                    e.submit(self._d.get_file_content, s['Id'],
                             '/etc/ssh/ssh_host_rsa_key.pub')))

        # Tell the master about all the mirrors.
        args = ['/set-mirrors.py']
        for ip, f_key in f_mirror_host_keys:
            key = f_key.result().strip()
            key = ' '.join(key.split()[0:2])
            args.extend([ip, key])
        self._d.execute(master_id, args)

        ldap_hostname, ldap_hostport = \
                self._d._get_host_hostname_port(ldap_state, '389/tcp')
        master_ssh_hostname, master_ssh_hostport = \
                self._d._get_host_hostname_port(master_state, '22/tcp')
        pulse_hostname, pulse_hostport = \
                self._d._get_host_hostname_port(pulse_state, '5672/tcp')

        self.ldap_uri = 'ldap://%s:%d/' % (ldap_hostname,
                                           ldap_hostport)

        fs = []
        with futures.ThreadPoolExecutor(4) as e:
            fs.append(e.submit(self.ldap.create_vcs_sync_login,
                               mirror_public_key))
            fs.append(e.submit(wait_for_amqp, pulse_hostname,
                               pulse_hostport, 'guest', 'guest'))
            fs.append(e.submit(wait_for_ssh, master_ssh_hostname,
                               master_ssh_hostport))
            # We already waited on the web nodes above. So only need to
            # wait on master here.
            h, p = self._d._get_host_hostname_port(master_state, '9092/tcp')
            fs.append(e.submit(wait_for_kafka, '%s:%s' % (h, p), 20))

        # Will re-raise exceptions.
        for f in fs:
            f.result()

        # Create Kafka topics.
        TOPICS = [
            ('pushdata', '8'),
            ('replicatedpushdata', '1'),
        ]
        fs = []
        with futures.ThreadPoolExecutor(2) as e:
            for topic, partitions in TOPICS:
                cmd = [
                    '/opt/kafka/bin/kafka-topics.sh',
                    '--create',
                    '--topic', topic,
                    '--partitions', partitions,
                    '--replication-factor', '3',
                    '--config', 'min.insync.replicas=2',
                    '--config', 'unclean.leader.election.enable=false',
                    '--config', 'max.message.bytes=104857600',
                    '--zookeeper', zookeeper_connect,
                ]
                fs.append(e.submit(self._d.execute, master_id, cmd,
                                   stdout=True))

        for f in futures.as_completed(fs):
            if 'Created topic' not in f.result():
                raise Exception('kafka topic not created')

        # There appears to be a race condition between the topic being
        # created and the topic being available. So we explicitly wait
        # for the topic to appear on all clients so processes within
        # containers don't need to wait.
        with futures.ThreadPoolExecutor(4) as e:
            fs = []
            for s in all_states:
                h, p = self._d._get_host_hostname_port(s, '9092/tcp')
                hostport = '%s:%s' % (h, p)
                for topic in TOPICS:
                    fs.append(e.submit(wait_for_kafka_topic, hostport,
                                       topic[0]))

            [f.result() for f in fs]

        self.ldap_image = ldap_image
        self.master_image = master_image
        self.web_image = web_image
        self.pulse_image = pulse_image
        self.ldap_id = ldap_id
        self.pulse_id = pulse_id
        self.master_id = master_id
        self.web_ids = web_ids
        self.pulse_hostname = pulse_hostname
        self.pulse_hostport = pulse_hostport
        self.master_ssh_hostname = master_ssh_hostname
        self.master_ssh_port = master_ssh_hostport
        self.master_host_rsa_key = master_host_rsa_key
        self.master_host_ed25519_key = master_host_ed25519_key
        self.web_urls = []
        self.kafka_hostports = []
        for s in all_states:
            hostname, hostport = self._d._get_host_hostname_port(s, '9092/tcp')
            self.kafka_hostports.append('%s:%d' % (hostname, hostport))
        for s in web_states:
            hostname, hostport = self._d._get_host_hostname_port(s, '80/tcp')
            self.web_urls.append('http://%s:%d/' % (hostname, hostport))
        self.zookeeper_connect = zookeeper_connect

        return self._write_state()

    def stop(self):
        """Stop the cluster.

        Containers will be shut down gracefully.
        """
        with futures.ThreadPoolExecutor(5) as e:
            e.submit(self._dc.stop, self.master_id)
            e.submit(self._dc.stop, self.ldap_id)
            e.submit(self._dc.stop, self.pulse_id)
            for i in self.web_ids:
                e.submit(self._dc.stop, i)

    def clean(self):
        """Clean the cluster.

        Containers will be shut down and removed. The state file will
        destroyed.
        """
        state = self._dc.inspect_container(self.master_id)

        with futures.ThreadPoolExecutor(4) as e:
            e.submit(self._dc.remove_container, self.master_id, force=True,
                     v=True)
            e.submit(self._dc.remove_container, self.ldap_id, force=True,
                     v=True)
            e.submit(self._dc.remove_container, self.pulse_id, force=True,
                     v=True)
            for i in self.web_ids:
                e.submit(self._dc.remove_container, i, force=True, v=True)

        for network in state['NetworkSettings']['Networks'].values():
            self._dc.remove_network(network['NetworkID'])

        try:
            os.unlink(self.state_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

        self.ldap_id = None
        self.pulse_id = None
        self.master_id = None
        self.web_ids = []
        self.ldap_uri = None
        self.pulse_hostname = None
        self.pulse_hostport = None
        self.master_ssh_hostname = None
        self.master_ssh_port = None
        self.kafka_hostports = []
        self.zookeeper_connect = None

    def _write_state(self):
        assert self.state_path
        s = {
                'ldap_image': self.ldap_image,
                'master_image': self.master_image,
                'web_image': self.web_image,
                'pulse_image': self.pulse_image,
                'ldap_id': self.ldap_id,
                'pulse_id': self.pulse_id,
                'master_id': self.master_id,
                'web_ids': self.web_ids,
                'ldap_uri': self.ldap_uri,
                'pulse_hostname': self.pulse_hostname,
                'pulse_hostport': self.pulse_hostport,
                'master_ssh_hostname': self.master_ssh_hostname,
                'master_ssh_port': self.master_ssh_port,
                'master_host_rsa_key': self.master_host_rsa_key,
                'master_host_ed25519_key': self.master_host_ed25519_key,
                'web_urls': self.web_urls,
                'kafka_hostports': self.kafka_hostports,
                'zookeeper_connect': self.zookeeper_connect,
        }
        with open(self.state_path, 'wb') as fh:
            json.dump(s, fh, sort_keys=True, indent=4)

        return s

    @property
    def ldap(self):
        assert self.ldap_uri
        return LDAP(self.ldap_uri, 'cn=admin,dc=mozilla', 'password')

    def get_mirror_ssh_keys(self, master_id=None):
        master_id = master_id or self.master_id

        with futures.ThreadPoolExecutor(4) as e:
            f_private_key = e.submit(self._d.get_file_content, master_id,
                                     '/etc/mercurial/mirror')
            f_public_key = e.submit(self._d.get_file_content, master_id,
                                    '/etc/mercurial/mirror.pub')
            f_host_ed25519_key = e.submit(self._d.get_file_content, master_id,
                                          '/etc/mercurial/ssh/ssh_host_ed25519_key.pub')
            f_host_rsa_key = e.submit(self._d.get_file_content, master_id,
                                      '/etc/mercurial/ssh/ssh_host_rsa_key.pub')

        host_ed25519_key = ' '.join(f_host_ed25519_key.result().split()[0:2])
        host_rsa_key = ' '.join(f_host_rsa_key.result().split()[0:2])

        return f_private_key.result(), f_public_key.result(), host_ed25519_key, host_rsa_key

    def create_repo(self, name, group='scm_level_1', no_generaldelta=False):
        """Create a repository on the cluster.

        ``path`` is the path fragment the repository would be accessed under
        at https://hg.mozilla.org. e.g. ``hgcustom/version-control-tools``.

        The repository will be owned by the specified ``group``.
        """
        cmd = ['/create-repo', name, group]

        if no_generaldelta:
            cmd.append('--no-generaldelta')

        return self._d.execute(self.master_id, cmd, stdout=True, stderr=True)

    def aggregate_code_coverage(self, destdir):
        master_map = {}
        for host, container in self.MASTER_FILE_MAP.items():
            master_map[container] = os.path.join(ROOT, host)

        for c in self._d.get_code_coverage(self.master_id, filemap=master_map):
            dest = os.path.join(destdir, 'coverage.%s' % uuid.uuid1())
            c.write_file(dest)
