# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import bugsy
import xmlrpclib

from rbbz.transports import bugzilla_transport

class Bugzilla(object):
    """High-level API to common Bugzilla tasks."""

    def __init__(self, base_url, username, password):
        xmlrpc_url = base_url + '/xmlrpc.cgi'
        rest_url = base_url + '/rest'

        transport = bugzilla_transport(xmlrpc_url)
        proxy = xmlrpclib.ServerProxy(xmlrpc_url, transport)
        proxy.User.login({'login': username, 'password': password})

        client = bugsy.Bugsy(username=username, password=password,
            bugzilla_url=rest_url)

        self.proxy = proxy
        self.client = client

    def create_bug(self, product, component, summary):
        bug = bugsy.Bug(self.client, product=product, component=component,
                summary=summary)
        self.client.put(bug)
