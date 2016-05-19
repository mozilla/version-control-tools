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
        with d.create_container(image, labels=['hgweb-chroot']) as state:
            cid = state['Id']
            d.client.start(cid, volumes_from=[vct_state['Name']])

            for s in d.client.attach(cid, stream=True, logs=True):
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
        'hgext/pushlog-legacy/buglink.py': '/var/hg/version-control-tools/hgext/pushlog-legacy/buglink.py',
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
        self._dc = docker.client
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

        with futures.ThreadPoolExecutor(5) as e:
            f_ldap_create = e.submit(self._dc.create_container, ldap_image,
                                     labels=['ldap'])
            f_pulse_create = e.submit(self._dc.create_container, pulse_image,
                                      labels=['pulse'])

            env = {
                'ZOOKEEPER_ID': '%d' % zookeeper_id,
                'KAFKA_BROKER_ID': '%d' % zookeeper_id,
            }
            zookeeper_id += 1

            if coverage:
                env['CODE_COVERAGE'] = '1'

            f_master_create = e.submit(self._dc.create_container,
                                       master_image,
                                       environment=env,
                                       entrypoint=['/entrypoint.py'],
                                       command=['/usr/bin/supervisord', '-n'],
                                       ports=[22, 2181, 2888, 3888, 9092],
                                       labels=['hgssh'])
            f_web_creates = []
            for i in range(web_count):
                env = {
                    'ZOOKEEPER_ID': '%d' % zookeeper_id,
                    'KAFKA_BROKER_ID': '%d' % zookeeper_id,
                }
                zookeeper_id += 1
                f_web_creates.append(e.submit(self._dc.create_container,
                                              web_image,
                                              environment=env,
                                              ports=[22, 80, 2181, 2888, 3888, 9092],
                                              entrypoint=['/entrypoint.py'],
                                              command=['/usr/bin/supervisord', '-n'],
                                              labels=['hgweb', 'hgweb%d' % i]))

            ldap_id = f_ldap_create.result()['Id']
            pulse_id = f_pulse_create.result()['Id']
            master_id = f_master_create.result()['Id']

            # Start LDAP and Pulse first because we need to link it to hg
            # containers.
            f_ldap_start = e.submit(self._dc.start, ldap_id,
                                    port_bindings={389: ldap_port})
            f_pulse_start = e.submit(self._dc.start, pulse_id,
                                     port_bindings={5672: pulse_port})
            f_ldap_start.result()
            f_pulse_start.result()

            ldap_state = self._dc.inspect_container(ldap_id)
            pulse_state = self._dc.inspect_container(pulse_id)

            self._dc.start(master_id,
                           links=[(ldap_state['Name'], 'ldap'),
                                  (pulse_state['Name'], 'pulse')],
                           port_bindings={
                               22: master_ssh_port,
                               9092: None,
                           })

            master_state = self._dc.inspect_container(master_id)

            web_ids = [f.result()['Id'] for f in f_web_creates]
            fs = []
            for i in web_ids:
                fs.append(e.submit(self._dc.start, i,
                                   links=[(master_state['Name'], 'master')],
                                   port_bindings={
                                       22: None,
                                       80: None,
                                       9092: None,
                                    }))
            [f.result() for f in fs]

            f_web_states = []
            for i in web_ids:
                f_web_states.append(e.submit(self._dc.inspect_container, i))

            web_states = [f.result() for f in f_web_states]

        all_states = [master_state] + web_states

        # ZooKeeper and Kafka can't be started until the endpoints of nodes in
        # the cluster are known. The entrypoint script waits for a file created
        # by a process execution to come into existence before these daemons
        # are started. So do this early after startup.
        zk_ips = [s['NetworkSettings']['IPAddress']
                  for s in [master_state] + web_states]
        zookeeper_hostports = ['%s:2888:3888' % ip for ip in zk_ips]
        zookeeper_connect = ','.join('%s:2181/hgmoreplication' % ip for ip in zk_ips)
        web_hostnames = [s['Config']['Hostname'] for s in web_states]

        with futures.ThreadPoolExecutor(web_count + 1) as e:
            for s in all_states:
                command = [
                    '/set-kafka-servers',
                    s['NetworkSettings']['IPAddress'],
                    '9092',
                    ','.join(web_hostnames),
                ] + zookeeper_hostports
                e.submit(self._d.execute, s['Id'], command)

        # Obtain replication SSH key from master. This key is random since it
        # is generated at container build time.
        with futures.ThreadPoolExecutor(4) as e:
            f_private_key = e.submit(self._d.get_file_content, master_id, '/etc/mercurial/mirror')
            f_public_key = e.submit(self._d.get_file_content, master_id, '/etc/mercurial/mirror.pub')
            f_master_host_ed25519_key = e.submit(self._d.get_file_content, master_id,
                                                 '/etc/mercurial/ssh/ssh_host_ed25519_key.pub')
            f_master_host_rsa_key = e.submit(self._d.get_file_content, master_id,
                                             '/etc/mercurial/ssh/ssh_host_rsa_key.pub')

        mirror_private_key = f_private_key.result()
        mirror_public_key = f_public_key.result()
        master_host_rsa_key = f_master_host_rsa_key.result()
        master_host_rsa_key = ' '.join(master_host_rsa_key.split()[0:2])
        master_host_ed25519_key = f_master_host_ed25519_key.result()
        master_host_ed25519_key = ' '.join(master_host_ed25519_key.split()[0:2])

        f_mirror_host_keys = []

        with futures.ThreadPoolExecutor(web_count + 1) as e:
            # Set SSH keys on hgweb instances.
            cmd = [
                '/set-mirror-key.py',
                mirror_private_key,
                mirror_public_key,
                master_state['NetworkSettings']['IPAddress'],
                # FUTURE this will need updated once hgweb supports ed25519 keys
                master_host_rsa_key,
            ]
            for i in web_ids:
                e.submit(self._d.execute, i, cmd)

            # Obtain host keys from mirrors.
            for s in web_states:
                f_mirror_host_keys.append((
                    s['NetworkSettings']['IPAddress'],
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

            for s in all_states:
                h, p = self._d._get_host_hostname_port(s, '9092/tcp')
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
        c = self._d.client
        with futures.ThreadPoolExecutor(5) as e:
            e.submit(c.stop, self.master_id)
            e.submit(c.stop, self.ldap_id)
            e.submit(c.stop, self.pulse_id)
            for i in self.web_ids:
                e.submit(c.stop, i)

    def clean(self):
        """Clean the cluster.

        Containers will be shut down and removed. The state file will
        destroyed.
        """
        c = self._d.client
        with futures.ThreadPoolExecutor(4) as e:
            e.submit(c.remove_container, self.master_id, force=True, v=True)
            e.submit(c.remove_container, self.ldap_id, force=True, v=True)
            e.submit(c.remove_container, self.pulse_id, force=True, v=True)
            for i in self.web_ids:
                e.submit(c.remove_container, i, force=True, v=True)

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

    def create_repo(self, name, level=1, generaldelta=False):
        """Create a repository on the cluster.

        ``path`` is the path fragment the repository would be accessed under
        at https://hg.mozilla.org. e.g. ``hgcustom/version-control-tools``.

        The repository will be owned by an appropriate ``scm_level_N`` group
        according to the ``level`` specified.
        """
        if level < 1 or level > 3:
            raise ValueError('level must be between 1 and 3')

        cmd = ['/create-repo', name, 'scm_level_%d' % level]

        if generaldelta:
            cmd.append('--generaldelta')

        return self._d.execute(self.master_id, cmd, stdout=True, stderr=True)

    def aggregate_code_coverage(self, destdir):
        master_map = {}
        for host, container in self.MASTER_FILE_MAP.items():
            master_map[container] = os.path.join(ROOT, host)

        for c in self._d.get_code_coverage(self.master_id, filemap=master_map):
            dest = os.path.join(destdir, 'coverage.%s' % uuid.uuid1())
            c.write_file(dest)
