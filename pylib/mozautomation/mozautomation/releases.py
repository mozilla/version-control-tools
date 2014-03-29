# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import json
import urllib2


class Releases(object):
    """Holds information about Firefox releases.

    Instances of this class are derived from the Releases API results.
    """
    def __init__(self, d):
        self._nightly_builds_by_type = {}
        self._release_builds_by_type = {}

        for products in d.get('nightly', []):
            for product, builds in products.items():
                by_type = self._nightly_builds_by_type.setdefault(product, {})

                for build in builds:
                    by_type.setdefault(build['build_type'], []).append(build)

        for products in d.get('releases', []):
            for product, builds in products.items():
                by_type = self._release_builds_by_type.setdefault(product, {})

                for build in builds:
                    by_type.setdefault(build['build_type'], []).append(build)

    def firefox_nightly_releases(self):
        """All releases for Firefox Nightly."""

        for release in self._nightly_builds_by_type.get('firefox', {})['Nightly']:
            if 'mozilla-central' in release['repository']:
                yield release



class ReleasesClient(object):
    """Client to the releases API.

    The releases API exposes information about builds on Firefox release
    channels.
    """
    def __init__(self, base_uri='http://releases-api.mozilla.org/', opener=None):
        self._base_uri = base_uri

        if opener is None:
            opener = urllib2.build_opener()

        self._opener = opener

    def releases(self):
        request = urllib2.Request('%sreleases' % self._base_uri, None)
        response = self._opener.open(request)

        return Releases(json.load(response))
