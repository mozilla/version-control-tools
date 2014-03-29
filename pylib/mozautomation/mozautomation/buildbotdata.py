# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import datetime
import json
import gzip
import re
import time
import urllib2

from collections import namedtuple
from io import BytesIO


BUILD_DATA_PREFIX = 'http://builddata.pub.build.mozilla.org/buildjson/'
BUILD_DATA_URL = BUILD_DATA_PREFIX + 'builds-%s.js.gz'

RE_BUILD_LISTING_ENTRY = re.compile(r'''
    ^<a\shref="(?P<path>[^"]+)">[^<]+<\/a>
    \s+
    (?P<date>\d{2}-[^-]+-\d{4}\s\d{2}:\d{2})
    \s+
    (?P<size>[\d-]+)
    $''', re.VERBOSE)


BuilderInfo = namedtuple('BuilderInfo', ('category', 'master_id', 'name',
    'slave_ids'))


class BuildInfo(object):
    """Describes buildbot data for a specific build/job"""

    def __init__(self, o):
        """Create from a JSON object describing the build."""

        self.id = o['id']
        self.builder_id = o['builder_id']
        self.build_number = o['buildnumber']
        self.master_id = o['master_id']
        self.slave_id = o['slave_id']
        self.start_time = o['starttime']
        self.end_time = o['endtime']
        self.reason = o['reason']
        self.request_ids = o['request_ids']
        self.result = o['result']
        self.properties = dict(o['properties'])

        self.duration = self.end_time - self.start_time


def available_buildbot_dump_files():
    """Obtain URLs of all buildbot dump files containing raw info for jobs."""

    html = urllib2.urlopen(BUILD_DATA_PREFIX).read()

    for line in html.splitlines():
        if not line.startswith('<'):
            continue

        match = RE_BUILD_LISTING_ENTRY.match(line)
        assert match

        d = match.groupdict()

        if d['path'].endswith('.tmp'):
            continue

        if d['size'] == '-':
            continue

        t = datetime.datetime.strptime(d['date'], '%d-%b-%Y %H:%M')

        yield d['path'], t, int(d['size'])


class BuildbotDump(object):
    """Represents information from a buildbot dump file."""

    def __init__(self, load_time=None):
        """Create a new instance.

        If day is specified as a datetime.date, the data for that day will be
        loaded into this object.
        """
        self._masters = {}
        self._slaves_by_id = {}
        self._slaves_by_name = {}
        self._builders_by_id = {}
        self._builds_by_id = {}

        # slave index to set of build IDs.
        self._builds_by_slave_id = {}
        self._builds_by_slave_name = {}

        if load_time:
            self.load_time(load_time)

    def load_time(self, t):
        datestring = time.strftime('%Y-%m-%d', time.gmtime(t))
        self._load_url(BUILD_DATA_URL % datestring)

    def load_date(self, d):
        self._load_url(BUILD_DATA_URL % d.isoformat())

    def _load_url(self, url):
        raw = urllib2.urlopen(url).read()

        if url.endswith('.gz'):
            raw = BytesIO(raw)
            raw = gzip.GzipFile(fileobj=raw).read()

        obj = json.loads(raw, encoding='utf-8')
        self.load_dump(obj)

    def load_dump(self, o):
        for master_id, master in o['masters'].items():
            master_id = int(master_id)

            self._masters[master_id] = (master['name'], master['url'])

        for slave_id, name in o['slaves'].items():
            slave_id = int(slave_id)
            self._slaves_by_id[slave_id] = name
            self._slaves_by_name[name] = slave_id

        for builder_id, builder in o['builders'].items():
            builder_id = int(builder_id)
            category = builder['category']
            master_id = builder['master_id']
            name = builder['name']
            slave_ids = set(builder['slaves'])

            self._builders_by_id[builder_id] = BuilderInfo(
                category=category, master_id=master_id, name=name,
                slave_ids=slave_ids)

        for build in o['builds']:
            b = BuildInfo(build)
            self._builds_by_id[b.id] = b
            slave_name = self._slaves_by_id[b.slave_id]

            self._builds_by_slave_id.setdefault(b.slave_id, set()).add(b.id)
            self._builds_by_slave_name.setdefault(slave_name, set()).add(b.id)

    @property
    def slave_names(self):
        return self._slaves_by_id.values()

    def slave_name(self, slave_id):
        return self._slaves_by_id[slave_id]

    def slave_groups(self):
        """Obtain information about groups of related slaves.

        Returns a dictionary mapping the group name to a set of slave names.
        """
        groups = {}
        for name in sorted(self.slave_names):
            group = '-'.join(name.split('-')[0:-1])

            groups.setdefault(group, set()).add(name)

        return groups

    def slave_efficiency(self, slave_id=None, slave_name=None):
        """Obtain a summary of activity on a given slave."""

        if slave_id:
            build_ids = self._builds_by_slave_id.get(slave_id, set())
        else:
            build_ids = self._builds_by_slave_name.get(slave_name, set())

        start_times = set()
        end_times = set()
        total_duration = 0

        for build_id in build_ids:
            build = self._builds_by_id[build_id]

            start_times.add(build.start_time)
            end_times.add(build.end_time)
            total_duration += build.duration

        if build_ids:
            earliest = min(start_times)
            latest = max(end_times)
            active_total = latest - earliest
            if active_total:
                active_percent = float(total_duration) / float(active_total)
            else:
                active_percent = 0.0
        else:
            active_percent = 0.0

        return (len(build_ids), total_duration, active_percent)

    def jobs_timeline(self):
        """Obtain a timeline of events for all jobs.

        This is a generator of tuples describing events as they occur over
        time.
        """

        events = []

        for build in self._builds_by_id.values():
            events.append((build.start_time, 'job_start', build))
            events.append((build.end_time, 'job_end', build))

        return sorted(events)

    def slave_timeline(self, slave_id=None, slave_name=None):
        """Obtain a timeline of events on a given slave."""

        if slave_id:
            build_ids = self._builds_by_slave_id.get(slave_id, set())
        else:
            build_ids = self._builds_by_slave_name.get(slave_name, set())

        for build_id in sorted(build_ids):
            build = self._builds_by_id[build_id]

            yield (build.start_time, 'job_start', build)
            yield (build.end_time, 'job_end', build)
