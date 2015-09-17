# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)


@CommandProvider
class TreestatusCommands(object):

    @Command('add-tree', category='treestatus',
             description='Add a new tree to treestatus')
    @CommandArgument('host', help='Host running treestatus')
    @CommandArgument('tree', help='Tree to add to treestatus')
    @CommandArgument('--user', required=False, default='sheriff@example.com',
                     help='Treestatus user')
    @CommandArgument('--password', required=False, default='password',
                     help='Treestatus password')
    def add_tree(self, host, tree, user=None, password=None):
        host = host.rstrip('/')
        r = requests.get(host + '/login', allow_redirects=False,
                         auth=(user, password))
        data = {
            'newtree': tree,
            'token': r.headers['x-treestatus-token'],
        }
        r = requests.post(host + '/mtree', data=data, auth=(user, password))
        assert r.status_code == 200

    @Command('set-status', category='treestatus',
             description='Set tree status')
    @CommandArgument('host', help='Host running treestatus')
    @CommandArgument('tree', help='Tree to close')
    @CommandArgument('status', choices=('open', 'closed', 'approval required'),
                     help='New tree status')
    @CommandArgument('--reason', default='',
                     help='Reason why the tree was closed')
    @CommandArgument('--remember', default='',
                     help='Remember previous tree state')
    @CommandArgument('--tags', default='Other',
                     help='Tag why tree was closed')
    @CommandArgument('--user', required=False, default='sheriff@example.com',
                     help='Treestatus user')
    @CommandArgument('--password', required=False, default='password',
                     help='Treestatus password')
    def set_status(self, host, tree, status, reason, remember, tags,
                   user=None, password=None):
        host = host.rstrip('/')
        r = requests.get(host + '/login', allow_redirects=False,
                         auth=(user, password))
        data = {
            'status': status,
            'tags': tags,
            'token': r.headers['x-treestatus-token'],
            'tree': tree,
            'reason': reason,
            'remember': remember,
        }
        r = requests.post(host + '/', data=data, auth=(user, password))
        assert r.status_code == 200
