# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

# TRACKING py3
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

import collections
import os
import re
import time

from kafka import SimpleClient
from kafka.common import KafkaUnavailableError

from mercurial import (
    pycompat,
)

# Holds a boolean indicating if a repo was filtered and the
# name of the rule that allowed/disallowed the filtering
RepoFilterResult = collections.namedtuple('RepoFilterResult', ('passes_filter', 'rule'))


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

    def get(self, section, option):
        return pycompat.sysstr(self.c.get(section, option))

    @property
    def hg_path(self):
        """Path to a hg executable."""
        if self.c.has_section('programs') and self.c.has_option('programs', 'hg'):
            return self.get('programs', 'hg')

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

    def filter(self, repo):
        """Returns a RepoFilterResult indicating if the repo should be filtered out
        of the set and which rule performed the include/exclude.

        If the repo was not touched by any rule, we default to disallowing the repo
        to be replicated. This rule is called "noinclude". If there were no
        filters defined at all, we pass the filter. This rule is called "nofilter".
        """
        if not self.has_filters:
            return RepoFilterResult(True, 'nofilter')

        if repo in self.path_includes:
            return RepoFilterResult(True, self.path_includes[repo])

        if repo in self.path_excludes:
            return RepoFilterResult(False, self.path_excludes[repo])

        includematch = self.include_regex.match(repo) if self.include_regex else None
        excludematch = self.exclude_regex.match(repo) if self.exclude_regex else None

        # Repo passes through filter if matching an include rule
        # and not matching an exclude rule
        if includematch and not excludematch:
            matchkeys = iter(includematch.groupdict().keys())
            return RepoFilterResult(True, next(matchkeys))

        # Return specific exclude rule if there was a match
        if excludematch:
            matchkeys = iter(excludematch.groupdict().keys())
            return RepoFilterResult(False, next(matchkeys))

        # Use "noinclude" if we didn't get a match for an include rule
        return RepoFilterResult(False, 'noinclude')

    def get_client_from_section(self, section, timeout=-1):
        """Obtain a KafkaClient from a config section.

        The config section must have a ``hosts`` and ``client_id`` option.
        An optional ``connect_timeout`` defines the connection timeout.

        ``timeout`` specifies how many seconds to retry attempting to connect
        to Kafka in case the initial connection failed. -1 indicates to not
        retry. This is useful when attempting to connect to a cluster that may
        still be coming online, for example.
        """
        hosts = self.get(section, 'hosts')
        client_id = self.get(section, 'client_id')
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
