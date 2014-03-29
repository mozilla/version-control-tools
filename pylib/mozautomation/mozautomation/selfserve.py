# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This file is a client to the self-serve HTTP API.

import json
import urllib2


class Branch(object):
    def __init__(self, client, name, meta=None):
        """Create a Branch bound to a client.

        The name is the name/identifier of the branch on the server.
        meta is metadata about the branch (returned from the branches() call on
        the main client. It is optional.

        Instances of this class are not meant to be instantiated outside this
        module.
        """
        self._client = client
        self.name = name

        if meta:
            self.graph_branches = meta['graph_branches']
            self.repo = meta['repo']
            self.repo_type = meta['repo']

    def builds(self):
        """Returns a list of builds on this branch."""
        return self._request()

    def rebuild(self, build_id):
        """Rebuild the build specified by its ID."""

    def cancel_build(self, build_id):
        """Cancel a build specified by its ID."""

    def build(self, build_id):
        """Obtain info about a build specified by its ID."""
        return self._request('build', build_id)

    def builders(self):
        """Return info on builders building for this branch."""
        return self._request('builders')

    def builder(self, builder):
        """Return info on a single bingler."""
        return self._request('builders', builder)

    def _request(self, *paths):
        return self._client._request(self.name, *paths)


class SelfServeClient(object):
    def __init__(self, uri, opener=None):
        self._uri = uri

        if not opener:
            opener = urllib2.build_opener()

        self._opener = opener

    def branches(self):
        """Returns all the branches as Branch instances."""
        for name, meta in self._request('branches').items():
            yield Branch(self, name, meta)

    def jobs(self):
        """Returns a list of past self-serve request."""
        return self._request('jobs')

    def get_job(self, job_id):
        """Return information about a specific job."""
        return self._request('jobs', job_id)

    def __getitem__(self, key):
        """Dictionary like access retrives branches."""
        return Branch(self, key)

    def _request(self, *paths):
        uri = self._uri
        for p in paths:
            uri += '/%s' % p

        request = urllib2.Request(uri, None,
            {'Accept': 'application/json'})

        response = self._opener.open(request)
        return json.load(response)


def get_mozilla_self_serve(username, password):
    uri = 'https://secure.pub.build.mozilla.org/buildapi/self-serve'

    handler = urllib2.HTTPBasicAuthHandler()
    handler.add_password(realm='Mozilla Contributors - LDAP Authentication',
        uri=uri, user=username, passwd=password)

    opener = urllib2.build_opener(handler)

    return SelfServeClient(uri, opener)

