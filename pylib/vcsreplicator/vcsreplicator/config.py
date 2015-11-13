# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from ConfigParser import RawConfigParser
import os
import time

from kafka.client import KafkaClient
from kafka.common import KafkaUnavailableError

from .consumer import Consumer
from .util import wait_for_topic


class Config(object):
    def __init__(self, filename=None):
        self.c = RawConfigParser()

        if filename:
            if not os.path.exists(filename):
                raise ValueError('config file does not exist: %s' % filename)

            self.c.read(filename)

        self._consumer = None

        if self.c.has_section('path_rewrites'):
            self._path_rewrites = self.c.items('path_rewrites')
        else:
            self._path_rewrites = []

        if self.c.has_section('pull_url_rewrites'):
            self._pull_url_rewrites = self.c.items('pull_url_rewrites')
        else:
            self._pull_url_rewrites = []

    def parse_wire_repo_path(self, path):
        """Parse a normalized repository path into a local path."""
        for source, dest in self._path_rewrites:
            if path.startswith(source):
                return path.replace(source, dest)

        return path

    def get_pull_url_from_repo_path(self, path):
        """Obtain a URL to be used for pulling from a local repo path."""
        lower = path.lower()
        for source, dest in self._pull_url_rewrites:
            if lower.startswith(source):
                return dest + path[len(source):]

        return None

    def get_client_from_section(self, section, timeout=-1):
        """Obtain a KafkaClient from a config section.

        The config section must have a ``hosts`` and ``client_id`` option.
        An optional ``connect_timeout`` defines the connection timeout.

        ``timeout`` specifies how many seconds to retry attempting to connect
        to Kafka in case the initial connection failed. -1 indicates to not
        retry. This is useful when attempting to connect to a cluster that may
        still be coming online, for example.
        """
        hosts = self.c.get(section, 'hosts')
        client_id = self.c.get(section, 'client_id')
        connect_timeout = 60
        if self.c.has_option(section, 'connect_timeout'):
            connect_timeout = self.c.getint(section, 'connect_timeout')

        start = time.time()
        while True:
            try:
                return KafkaClient(hosts, client_id=client_id,
                        timeout=connect_timeout)
            except KafkaUnavailableError:
                if timeout == -1:
                    raise

            if time.time() - start > timeout:
                raise Exception('timeout reached trying to connect to Kafka')

            time.sleep(0.1)

    @property
    def consumer(self):
        if not self._consumer:
            client = self.get_client_from_section('consumer', timeout=30)
            topic = self.c.get('consumer', 'topic')
            group = self.c.get('consumer', 'group')

            wait_for_topic(client, topic, timeout=30)
            self._consumer = Consumer(client, group, topic, None)

        return self._consumer
