# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import json
import urllib2

from time import strptime


class TreeStatus(object):
    """Represents the status of an individual tree."""

    APPROVAL_REQUEST = 'approval required'
    OPEN = 'open'
    CLOSED = 'closed'

    def __init__(self, d):
        self.status = None
        self.motd = None
        self.tree = None
        self.reason = None

        for k in d:
            if k == 'status':
                self.status = d[k]
            elif k == 'message_of_the_day':
                self.motd = d[k]
            elif k == 'tree':
                self.tree = d[k]
            elif k == 'reason':
                self.reason = d[k]
            else:
                raise Exception('Unknown key in Tree Status response: %s' % k)

    @property
    def open(self):
        return self.status == self.OPEN

    @property
    def closed(self):
        return self.status == self.CLOSED

    @property
    def approval_required(self):
        return self.status == self.APPROVAL_REQUIRED


class TreeLog(object):
    """Represents a change in a tree's status."""
    def __init__(self, d):
        self.reason = d['reason'] or None
        self.tags = set(d['tags']) if d['tags'] else set()
        self.tree = d['tree']
        self.who = d['who']
        # FUTURE return a datetime with appropriate timezone info set.
        self.when = strptime(d['when'], '%Y-%m-%dT%H:%M:%S')


class TreeStatusClient(object):
    """Client to the Mozilla Tree Status API.

    The tree status API controls whether Mozilla's main source repositories are
    open or closed.
    """

    def __init__(self, base_uri='https://treestatus.mozilla.org/', opener=None):
        self._base_uri = base_uri

        if opener is None:
            opener = urllib2.build_opener()

        self._opener = opener

    def _request(self, path):
        request = urllib2.Request('%s%s' % (self._base_uri, path), None)
        response = self._opener.open(request)
        return json.load(response)

    def all(self):
        """Obtain the status of all trees.

        Returns a dict of tree names to TreeStatus instances.
        """

        o = self._request('?format=json')
        trees = {}
        for k, v in o.items():
            trees[k] = TreeStatus(v)

        return trees

    def tree_status(self, tree):
        """Obtain the status of a single tree.

        Returns a TreeStatus instance.
        """
        o = self._request('%s?format=json' % tree)
        return TreeStatus(o)

    def tree_logs(self, tree):
        o = self._request('%s/logs?format=json' % tree)

        for d in o['logs']:
            yield TreeLog(d)

