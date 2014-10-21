# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import xmlrpclib

import bugsy

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

from rbbz.transports import bugzilla_transport

@CommandProvider
class BugzillaCommands(object):
    def __init__(self, context):
        url = os.environ['BUGZILLA_URL'] + '/rest'
        username = os.environ['BUGZILLA_USERNAME']
        password = os.environ['BUGZILLA_PASSWORD']

        xmlrpcurl = os.environ['BUGZILLA_URL'] + '/xmlrpc.cgi'
        transport = bugzilla_transport(xmlrpcurl)

        proxy = xmlrpclib.ServerProxy(xmlrpcurl, transport)
        proxy.User.login({'login': username, 'password': password})

        client = bugsy.Bugsy(username=username, password=password,
                bugzilla_url=url)

        self.proxy = proxy
        self.client = client

    @Command('create-bug', category='bugzilla',
            description='Create a new bug')
    @CommandArgument('product', help='Product to create bug in')
    @CommandArgument('component', help='Component to create bug in')
    @CommandArgument('summary', help='Bug summary')
    def create_bug(self, product, component, summary):
        bug = bugsy.Bug(self.client, product=product, component=component,
                summary=summary)
        self.client.put(bug)
