# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import json
import urllib2

from time import strptime


class TreeStatus(object):
    """Represents the status of an individual tree."""

    APPROVAL_REQUEST = b"approval required"
    OPEN = b"open"
    CLOSED = b"closed"

    def __init__(self, d):
        self.status = None
        self.motd = None
        self.tree = None
        self.reason = None
        self.tags = None

        for k in d:
            if k == b"status":
                self.status = d[k]
            elif k == b"message_of_the_day":
                self.motd = d[k]
            elif k == b"tree":
                self.tree = d[k]
            elif k == b"reason":
                self.reason = d[k]
            elif k == "tags":
                self.tags = d[k]
            elif k in ("log_id",):
                pass
            else:
                raise Exception("Unknown key in Tree Status response: %s" % k)

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
        self.reason = d[b"reason"] or None
        self.tags = set(d[b"tags"]) if d[b"tags"] else set()
        self.tree = d[b"tree"]
        self.who = d[b"who"]
        # FUTURE return a datetime with appropriate timezone info set.
        self.when = strptime(d[b"when"], b"%Y-%m-%dT%H:%M:%S")


class TreeStatusClient(object):
    """Client to the Mozilla Tree Status API.

    The tree status API controls whether Mozilla's main source repositories are
    open or closed.
    """

    def __init__(
        self,
        base_uri=b"https://treestatus.prod.lando.prod.cloudops.mozgcp.net/",
        opener=None,
    ):
        self._base_uri = base_uri

        if opener is None:
            opener = urllib2.build_opener()

        self._opener = opener

    def _request(self, path):
        request = urllib2.Request(b"%s%s" % (self._base_uri, path), None)
        response = self._opener.open(request)
        return json.load(response)[b"result"]

    def all(self):
        """Obtain the status of all trees.

        Returns a dict of tree names to TreeStatus instances.
        """

        o = self._request(b"/trees")
        trees = {}
        for k, v in o.items():
            trees[k] = TreeStatus(v)

        return trees

    def tree_status(self, tree):
        """Obtain the status of a single tree.

        Returns a TreeStatus instance.
        """
        o = self._request(b"/trees/%s" % tree)
        return TreeStatus(o)

    def tree_logs(self, tree):
        o = self._request(b"/trees/%s/logs" % tree)

        for d in o:
            yield TreeLog(d)
