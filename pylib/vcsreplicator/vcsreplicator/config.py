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

    def get_client_from_section(self, section):
        """Obtain a KafkaClient from a config section.

        The config section must have a ``hosts`` and ``client_id`` option.
        An optional ``connect_timeout`` defines the connection timeout.
        """
        hosts = self.c.get(section, 'hosts')
        client_id = self.c.get(section, 'client_id')
        timeout = 60
        if self.c.has_option(section, 'connect_timeout'):
            timeout = self.c.getint(section, 'connect_timeout')

        return KafkaClient(hosts, client_id=client_id, timeout=timeout)

    @property
    def consumer(self):
        if not self._consumer:
            # We manually catch KafkaUnavailableError because it occurs when
            # all hosts in the cluster are not responding. We shouldn't see
            # this in production. However, it does happen quite a lot when
            # Docker containers start. It is easiest to not have the log spam.
            start = time.time()
            while True:
                try:
                    client = self.get_client_from_section('consumer')
                    break
                except KafkaUnavailableError:
                    pass

                if time.time() - start > 30:
                    raise Exception('timeout reached trying to connect to Kafka')

                time.sleep(0.1)

            topic = self.c.get('consumer', 'topic')
            group = self.c.get('consumer', 'group')

            # Wait for topic to exist before trying to instantiate consumer.
            # There is a ``ensure_topic_exists`` on KafkaClient. However, it
            # will create the topic. We don't want that.
            start = time.time()
            while not client.has_metadata_for_topic(topic):
                if time.time() - start > 30:
                    raise Exception('timeout reached waiting for topic')

                time.sleep(0.1)

                # Don't pass topic name to function or it will attempt to
                # create.
                client.load_metadata_for_topics()

            self._consumer = Consumer(client, group, topic, None)

        return self._consumer
