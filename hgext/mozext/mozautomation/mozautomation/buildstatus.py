# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import json
import urllib2


PLATFORMS = dict(
    ANDROID_4_0_PANDA=('Android 4.0', 10),
    ANDROID_ARMV6_TEGRA_250=('Android 2.2 Armv6', 10),
    ANDROID_TEGRA_250=('', 10),
    ANDROID_TEGRA_250_NOION=('', 10),
    B2G_EMULATOR_VM=('B2G Emu (VM)', 10),
    B2G_EMULATOR=('B2G Emu', 10),
    OSX_10_8=('OS X 10.8', 10),
    OSX_10_7=('OS X 10.7', 10),
    OSX_10_6=('OS X 10.6', 10),
    UBUNTU_HW_1204_64=('Ubuntu64', 10),
    UBUNTU_HW_1204_32=('Ubuntu32', 10),
    UBUNTU_VM_1204_64=('Ubuntu64', 10),
    UBUNTU_VM_1204_32=('Ubuntu32', 10),
    WINDOWS_XP_32=('WinXP', 10),
    WINDOWS_7_32=('Win7', 10),
    WINDOWS_8=('Win8', 10),
)

PREFIXES = [
    ('Windows XP 32-bit', 'WINDOWS_XP_32'),
    ('Windows 7 32-bit', 'WINDOWS_7_32'),
    ('WINNT 6.2', 'WINDOWS_8'),
    ('Ubuntu HW 12.04 x64', 'UBUNTU_HW_1204_64'),
    ('Ubuntu HW 12.04', 'UBUNTU_HW_1204_32'),
    ('Ubuntu VM 12.04 x64', 'UBUNTU_VM_1204_64'),
    ('Ubuntu VM 12.04', 'UBUNTU_VM_1204_32'),
    ('Rev5 MacOSX Mountain Lion 10.8', 'OSX_10_8'),
    ('Rev4 MacOSX Lion 10.7', 'OSX_10_7'),
    ('Rev4 MacOSX Snow Leopard 10.6', 'OSX_10_6'),
    ('Android 4.0 Panda', 'ANDROID_4_0_PANDA'),
    ('Android Armv6 Tegra 250', 'ANDROID_ARMV6_TEGRA_250'),
    ('Android Tegra 250', 'ANDROID_TEGRA_250'),
    ('b2g_emulator_vm', 'B2G_EMULATOR_VM'),
    ('b2g_emulator', 'B2G_EMULATOR'),

    # This is where it starts to get a little inconsistent.
    ('Android no-ionmonkey Tegra 250', 'ANDROID_TEGRA_250_NOION'),
    ('Android no-ionmonkey', 'ANDROID_TEGRA_250_NOION'),
]

TREES = {'mozilla-central', 'mozilla-inbound'}

JOBS = {
    'build',
    'chromez',
    'crashtest',
    'crashtest-1',
    'crashtest-2',
    'crashtest-3',
    'crashtest-ipc',
    'dirtypaint',
    'dromaeojs',
    'jetpack',
    'jsreftest',
    'jsreftest-1',
    'jsreftest-2',
    'jsreftest-3',
    'hsreftest',
    'marionette',
    'marionette-webapi',
    'mochitest-1',
    'mochitest-2',
    'mochitest-3',
    'mochitest-4',
    'mochitest-5',
    'mochitest-6',
    'mochitest-7',
    'mochitest-8',
    'mochitest-9',
    'mochitest-browser-chrome',
    'mochitest-gl',
    'mochitest-metro-chrome',
    'mochitest-other',
    'other',
    'plain-reftest-1',
    'plain-reftest-2',
    'plain-reftest-3',
    'plain-reftest-4',
    'reftest',
    'reftest-1',
    'reftest-2',
    'reftest-3',
    'reftest-4',
    'reftest-5',
    'reftest-6',
    'reftest-7',
    'reftest-8',
    'reftest-9',
    'reftest-10',
    'reftest-ipc',
    'reftest-no-accel',
    'remote-tp4m_chochrome',
    'remote-tp4m_nochrome',
    'remote-trobocheck2',
    'remote-trobopan',
    'remote-troboprovider',
    'remote-ts',
    'remote-tsvg',
    'robocop-1',
    'robocop-2',
    'svgr',
    'talos',
    'tp5o',
    'xpcshell',
}


def parse_builder_name(b):
    """Parse a builder name into metadata."""

    platform = None

    remaining = ''

    for prefix, key in PREFIXES:
        if b.startswith(prefix):
            platform = key
            remaining = b[len(prefix)+1:]
            break

    tree = None
    opt_level = None
    job_type = None
    props = set(remaining.split())
    try:
        props.remove('test')
    except KeyError:
        pass

    for t in TREES:
        if t in props:
            tree = t
            props.remove(t)
            break

    if 'opt' in props:
        opt_level = 'opt'
    elif 'debug' in props:
        opt_level = 'debug'
    elif 'pgo' in props:
        opt_level = 'pgo'

    if opt_level:
        props.remove(opt_level)

    for job in JOBS:
        if job in props:
            job_type = job
            props.remove(job)


class JobResult(object):
    """Represents the result of an individual automation job."""

    def __init__(self, d):
        self.build_id = d['_id']
        self.builder_name = d['buildername']
        self.slave = d['slave']
        self.result = d['result']
        self.start_time = int(d['starttime'])
        self.end_time = int(d['endtime'])
        self.log = d['log']
        self.notes = d['notes']


class BuildStatusResult(object):
    def __init__(self, o):
        self.jobs = []
        for job in o:
            self.jobs.append(JobResult(job))


class BuildStatusClient(object):
    """Client to interface with build status API."""

    def __init__(self, base_uri='https://tbpl.mozilla.org/php/'):
        self._base_uri = base_uri
        self._opener = urllib2.build_opener()

    def revision_builds(self, repo, changeset):
        """Obtain the build status for a single changeset in a repository."""

        # The API only accepts 12 digit short form changesets.
        if len(changeset) > 12:
            changeset = changeset[0:12]

        request = urllib2.Request('%sgetRevisionBuilds.php?branch=%s&rev=%s' %
            (self._base_uri, repo, changeset))

        response = self._opener.open(request)

        return BuildStatusResult(json.load(response))
