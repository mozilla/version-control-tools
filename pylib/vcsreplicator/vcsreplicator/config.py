# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from ConfigParser import RawConfigParser
import os
import re
import time

from kafka import SimpleClient
from kafka.common import KafkaUnavailableError


def create_namedgroup(name, rule):
    '''Returns a regex group with name `name` that must match `rule`
    '''
    return '(?P<{name}>{rule})'.format(
        name=name,
        rule=rule
    )


class Config(object):
    """Hold configuration state and utility functions related to config state.

    This is kind of a catch all for functionality related to the current
    configuration.
    """
    def __init__(self, filename=None):
        self.c = RawConfigParser()

        if filename:
            if not os.path.exists(filename):
                raise ValueError('config file does not exist: %s' % filename)

            self.c.read(filename)

        if self.c.has_section('path_rewrites'):
            self._path_rewrites = self.c.items('path_rewrites')
        else:
            self._path_rewrites = []

        if self.c.has_section('pull_url_rewrites'):
            self._pull_url_rewrites = self.c.items('pull_url_rewrites')
        else:
            self._pull_url_rewrites = []

        if self.c.has_section('public_url_rewrites'):
            self._public_url_rewrites = self.c.items('public_url_rewrites')
        else:
            self._public_url_rewrites = []

        if self.c.has_section('replicationpathrewrites'):
            self._replication_path_rewrites = self.c.items('replicationpathrewrites')
        else:
            self._replication_path_rewrites = []

        if self.c.has_section('replicationrules'):
            re_includes, re_excludes = [], []
            self.path_includes, self.path_excludes = {}, {}
            for key, value in self.c.items('replicationrules'):
                (behaviour, name), (ruletype, rule) = key.split('.'), value.split(':')

                if ruletype == 're':
                    # Decide which list is correct and append to it
                    restore = re_includes if behaviour == 'include' else re_excludes
                    restore.append((name, rule))

                elif ruletype == 'path':
                    exstore = self.path_includes if behaviour == 'include' else self.path_excludes
                    exstore[rule] = name
                else:
                    raise Exception('bad ruletype %s' % ruletype)

            # Create the in/out rules as an `or` of all the rules
            includes_string = '|'.join(
                create_namedgroup(name, rule)
                for name, rule in re_includes
            )
            excludes_string = '|'.join(
                create_namedgroup(name, rule)
                for name, rule in re_excludes
            )

            self.include_regex = re.compile(includes_string) if includes_string else None
            self.exclude_regex = re.compile(excludes_string) if excludes_string else None

            self.has_filters = bool(self.path_includes or self.path_excludes or self.include_regex or self.exclude_regex)
        else:
            self.has_filters = False

    @property
    def hg_path(self):
        """Path to a hg executable."""
        if self.c.has_section('programs') and self.c.has_option('programs', 'hg'):
            return self.c.get('programs', 'hg')

        return 'hg'

    def parse_wire_repo_path(self, path):
        """Parse a normalized repository path into a local path."""  
        for source, dest in self._path_rewrites:
            if path.startswith(source):
                return path.replace(source, dest)

        return path

    def get_replication_path_rewrite(self, path):
        """Parse a local path into a wire path"""
        for source, dest in self._replication_path_rewrites:
            if path.startswith(source):
                return dest + path[len(source):]

        return None

    def get_pull_url_from_repo_path(self, path):
        """Obtain a URL to be used for pulling from a local repo path."""
        for source, dest in self._pull_url_rewrites:
            if path.startswith(source):
                return dest + path[len(source):]

        return None

    def get_public_url_from_wire_path(self, path):
        """Obtain a URL to be used for public advertisement from a wire protocol path."""
        for source, dest in self._public_url_rewrites:
            if path.startswith(source):
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
                return SimpleClient(hosts, client_id=client_id,
                                   timeout=connect_timeout)
            except KafkaUnavailableError:
                if timeout == -1:
                    raise

            if time.time() - start > timeout:
                raise Exception('timeout reached trying to connect to Kafka')

            time.sleep(0.1)
