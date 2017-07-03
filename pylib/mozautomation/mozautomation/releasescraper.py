# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Functionality for discovering Firefox releases.

This module contains code for scraping archive.mozilla.org and other
sites for information about Firefox releases.
"""

from __future__ import absolute_import, unicode_literals

import collections
import datetime
import distutils.version
import re

import concurrent.futures as futures
import requests
import requests.adapters

NIGHTLY_ARCHIVE_URL = 'https://archive.mozilla.org/pub/firefox/nightly'
RELEASES_ARCHIVE_URL = 'https://archive.mozilla.org/pub/firefox/releases'

RE_NIGHTLY_MONTH_ENTRY = re.compile(r'''
    <a\shref="/pub/firefox/nightly/\d{4}/\d{2}/
    # %Y-%m-%d
    (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})
    # optional -HH-MM-SS or -HH time component
    (?:-\d{2}(?:-\d{2}-\d{2})?)?
    -(?P<build>[^/]+)
    /">(?P<path>[^<]+)</a>
''', re.VERBOSE)

RE_ARCHIVE_FILENAMES = re.compile(r'''
    <a\shref="(?P<fullpath>[^"]+)">(?P<path>[^\.][^<]+)</a>
''', re.VERBOSE)

NIGHTLY_JSON_FILES = {
    'linux32': re.compile('^firefox-.*\.linux-i686\.json$'),
    'linux64': re.compile('^firefox-.*\.linux-x86_64\.json$'),
    'linux64-asan': re.compile('^firefox-.*\.linux-x86_64-asan\.json$'),
    'mac': re.compile('^firefox-.*\.mac(64)?\.json$'),
    'win32': re.compile('^firefox-.*\.win32\.json$'),
    'win64': re.compile('^firefox-.*\.win64(-x86_64)?\.json$'),
}

NIGHTLY_TEXT_FILES = {
    'linux32': re.compile('^firefox-.*\.linux-i686\.txt$'),
    'linux64': re.compile('^firefox-.*\.linux-x86_64\.txt$'),
    'linux64-asan': re.compile('^firefox-.*-x86_64-asan\.txt$'),
    'mac': re.compile('^firefox-.*\.mac(64)?\.txt$'),
    'mac-shark': re.compile('^firefox-.*\.mac-shark\.txt$'),
    'win32': re.compile('^firefox-.*\.win32\.txt$'),
    'win64': re.compile('^firefox-.*\.win64(-x86_64)?\.txt$'),
}

# Keys from above dicts that should be filtered out.
NIGHTLY_IGNORE_PLATFORMS = {
    'linux64-asan',
    'mac-shark',
}

RE_APP_VERSION = re.compile('^firefox-(?P<version>.+)\.en-US\.')

# URLs where we're unable to find builds due to valid reasons.
INVALID_NIGHTLY_URLS = {
    'https://archive.mozilla.org/pub/firefox/nightly/2012/01/2012-01-21-11'
    '-34-34-mozilla-central/',
    'https://archive.mozilla.org/pub/firefox/nightly/2012/05/2012-05-28-03'
    '-05-18-mozilla-central/',
}

TAGS_REPOS = [
    ('releases/mozilla-beta', 'beta'),
    ('releases/mozilla-release', 'release'),
]

RELEASES_PLATFORMS = {
    'linux32': 'linux-i686',
    'linux64': 'linux-x86_64',
    'mac': 'mac',
    'win32': 'win32',
    'win64': 'win64',
}

# Tags that exist but we don't have releases for.
MISSING_RELEASES = {
    '3.1a1',
    '3.1a2',
    '5.0b4',
    '13.0.2',
    '40.0.1',
}

RE_TAG = re.compile('^FIREFOX_(?P<version>.*)_RELEASE$')


def get_session():
    session = requests.Session()
    session.headers['User-Agent'] = 'mozautomation/Firefox Release Scraper'

    return session


def find_nightly_builds(start_day, end_day=None):
    """Find all Nightly builds for a given date range.

    This function opens a pool of HTTP sockets and spiders appropriate
    sites for references to builds for the date range specified. If no
    ``end_day`` is set, defaults to UTC today.

    This function should be able to find Nightly builds back to at least
    April 2010.

    This function is a generator of dicts describing each found build. Dicts
    have the following keys:

    channel
       The release channel. Always ``nightly``.
    platform
       The build platform. e.g. ``linux64`` or ``win32``.
    build_id
       The build ID. Looks like a timestamp. Should be unique per
       (platform, app_version).
    app_version
       The application version string.
    revision
       Mercurial revision build was produced from. May be 12 or 40 characters.
       See ``ensure_full_revision()`` for how to normalize this to the full
       hash.
    day
       A ``datetime.date`` corresponding to the day of the build. Timezone is
       undefined.
    archive_url
       Where build artifacts can be obtained.
    """

    if not end_day:
        end_day = datetime.datetime.utcnow().date()

    session = get_session()

    with futures.ThreadPoolExecutor(requests.adapters.DEFAULT_POOLSIZE) as e:
        day = start_day

        # Load monthly pages to find links to builds.
        months = set()
        while day <= end_day:
            months.add(day.strftime('%Y/%m'))
            day += datetime.timedelta(days=1)

        month_fs = []
        for month in sorted(months):
            url = '%s/%s/' % (NIGHTLY_ARCHIVE_URL, month)
            month_fs.append(e.submit(session.get, url))
            day += datetime.timedelta(days=1)

        builds_by_day = collections.defaultdict(list)
        for f in futures.as_completed(month_fs):
            r = f.result()
            if r.status_code != 200:
                continue

            for m in RE_NIGHTLY_MONTH_ENTRY.finditer(r.text):
                groups = m.groupdict()
                day = datetime.date(int(groups['year']), int(groups['month']),
                                    int(groups['day']))
                builds_by_day[day].append((groups['build'], groups['path']))

        build_fs = []

        for day, builds in sorted(builds_by_day.iteritems()):
            for build, path in builds:
                if build != 'mozilla-central':
                    continue

                url = '%s/%s/%s' % (NIGHTLY_ARCHIVE_URL, day.strftime('%Y/%m'),
                                    path)
                build_fs.append(e.submit(session.get, url))

        release_fs = []

        for f in futures.as_completed(build_fs):
            r = f.result()
            # We found a link. So index should exist.
            assert r.status_code == 200

            found_build = False
            for m in RE_ARCHIVE_FILENAMES.finditer(r.text):
                info = match_archive_build_file(r.url, m)
                if not info:
                    continue

                found_build = True

                if info['platform'] in NIGHTLY_IGNORE_PLATFORMS:
                    continue

                assert info['path'].startswith('/pub/firefox/nightly/')
                normpath = info['path'][len('/pub/firefox/nightly/'):]
                url = '%s/%s' % (NIGHTLY_ARCHIVE_URL, normpath)

                release_fs.append((info['platform'],
                                   e.submit(session.get, url)))

            if not found_build:
                # This could be a bug in this script. Filter out special cases
                # that are known failures and emit warnings for remaining.
                if r.url in INVALID_NIGHTLY_URLS:
                    continue

                if all('_test' in m.group('path')
                       for m in RE_ARCHIVE_FILENAMES.finditer(r.text)):
                    continue

                if all(m.group('path').endswith('.txt.gz')
                       for m in RE_ARCHIVE_FILENAMES.finditer(r.text)):
                    continue

                print('no build info for %s' % r.url)
                for m in RE_ARCHIVE_FILENAMES.finditer(r.text):
                    print('\t%s' % m.group('path'))
                continue

        try:
            for platform, f in release_fs:
                r = f.result()

                if r.status_code != 200:
                    print('HTTP %s from %s' % (r.status_code, r.url))
                    continue

                build = get_build_from_archive_file(platform, r)
                if build:
                    yield build
        except Exception:
            # Cancel all pending futures so we abort immediately.
            for platform, f in release_fs:
                f.cancel()

            raise


def match_archive_build_file(url, m):
    fullpath, path = m.group('fullpath'), m.group('path')

    # JSON is the preferred method for finding build info. Look for it
    # first.
    if path.endswith('.json'):
        # Ignore JSON files that aren't build metadata.
        if path.endswith(('.mozinfo.json', '.test_packages.json')):
            return

        if path == 'test_packages.json':
            return

        for platform, expr in NIGHTLY_JSON_FILES.items():
            if expr.match(path):
                return {
                    'platform': platform,
                    'path': fullpath,
                }

        #print(path)

    elif path.endswith('.txt'):
        for platform, expr in NIGHTLY_TEXT_FILES.items():
            if expr.match(path):
                return {
                    'platform': platform,
                    'path': fullpath,
                }

        if path.startswith(('minefield', 'mozilla-nightly')):
            return

        if path.endswith('_info.txt'):
            return

        #print('%s %s' % (path, url))


def get_build_from_archive_file(platform, r):
    """Obtain a build object from a HTTP response.

    The requested URL corresponds to a JSON or text build info file.
    """
    if r.url.endswith('.json'):
        release = r.json()

        build_id = release['buildid']
        app_version = release['moz_app_version']
        revision = release['moz_source_stamp']
    elif r.url.endswith('.txt'):
        # Format is one of the following:
        #
        #   <buildid> <revision>
        #
        #   <buildid>
        #   <revision url>
        lines = r.text.splitlines()
        if len(lines) == 1:
            # linux64-asan builds have invalid text files (they don't
            # list the revision/url). But they should be filtered away
            # above.
            build_id, revision = lines[0].split()
        elif len(lines) == 2:
            build_id, url = lines
            assert url.startswith(('http://hg.mozilla.org/',
                                   'https://hg.mozilla.org/'))
            revision = url[url.rindex('/') + 1:]
        else:
            print('unknown text file format for %s' % r.url)
            print(r.text)
            return None

        path = r.url[r.url.rindex('/') + 1:]
        m = RE_APP_VERSION.match(path)
        if not m:
            print('could not determine app version: %s' % path)
            return None

        app_version = m.group('version')

    year = int(build_id[0:4])
    month = int(build_id[4:6])
    day = int(build_id[6:8])

    return {
        'channel': 'nightly',
        'platform': platform,
        'build_id': build_id,
        'app_version': app_version,
        'revision': revision,
        'day': datetime.date(year, month, day),
        'archive_url': r.url[:r.url.rindex('/') + 1],
    }


def ensure_full_revision(releases, local_hg_repo):
    """Expand full Mercurial revisions.

    Old release metadata only uses the abbreviated 12 character changeset hash.
    We want to normalize all revisions to the full 40 character hash.

    This function takes an iterable of release dicts and a path to a local hg
    repo and expands all revisions.

    A clone of the mozilla-unified repo should be sufficient to expand
    revisions.
    """
    import hglib

    with hglib.open(local_hg_repo, encoding='utf-8') as repo:
        for release in releases:
            if len(release['revision']) != 40:
                ctx = repo[release['revision']]
                release['revision'] = ctx.node()

            yield release


def find_builds_from_tags():
    session = get_session()

    with futures.ThreadPoolExecutor(requests.adapters.DEFAULT_POOLSIZE) as e:
        archive_fs = []
        seen_tags = set()

        # Need to process in order because we only process each tag once.
        for repo, channel in TAGS_REPOS:
            url = 'https://hg.mozilla.org/%s/json-tags' % repo

            r = session.get(url)
            if r.status_code != 200:
                raise Exception('unexpected non-200 from %s' % url)

            for entry in r.json()['tags']:
                m = RE_TAG.match(entry['tag'])
                if not m:
                    continue

                if entry['tag'] in seen_tags:
                    continue
                seen_tags.add(entry['tag'])

                version = m.group('version')

                if 'a' in version:
                    sep = 'a'
                    major, sub = version.split('a')
                elif 'b' in version:
                    sep = 'b'
                    major, sub = version.split('b')
                else:
                    major = version
                    sub = None

                major = major.replace('_', '.')
                app_version = major
                if sub:
                    app_version += '%s%s' % (sep, sub)

                # Some releases are tagged but were never released. Skip them.
                if app_version in MISSING_RELEASES:
                    continue

                # There are no build ids for release builds. Construct a
                # dummy one from the tag date.
                td = datetime.timedelta(seconds=entry['date'][0])
                dt = datetime.datetime(1970, 1, 1) + td
                day = dt.date()

                build_id = dt.strftime('%Y%m%d%H%M%S')

                for platform, archive_platform in RELEASES_PLATFORMS.items():
                    # win64 not produced until release 42.
                    if platform == 'win64':
                        v = distutils.version.StrictVersion
                        ours = v(major) if '.' in major else v('%s.0' % major)

                        if ours < v('42.0'):
                            continue

                    archive_url = '%s/%s/%s/' % (RELEASES_ARCHIVE_URL,
                                                 app_version, archive_platform)

                    build = {
                        'revision': entry['node'],
                        'tag': entry['tag'],
                        'channel': channel,
                        'app_version': app_version,
                        'platform': platform,
                        'archive_url': archive_url,
                        'build_id': build_id,
                        'day': day,
                    }

                    archive_fs.append((build,
                                       e.submit(session.get, archive_url)))

        for build, f in archive_fs:
            r = f.result()
            if r.status_code != 200:
                # We shouldn't hit this.
                print('could not find release %s %s from tag %s' % (
                    build['app_version'], build['platform'], build['tag']))
                continue

            yield build
