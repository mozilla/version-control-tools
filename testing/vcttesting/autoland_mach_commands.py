# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import requests

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

@CommandProvider
class AutolandCommands(object):

    @Command('post-autoland-job', category='autoland',
        description='Post a job to autoland')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('tree', help='Source tree of the revision')
    @CommandArgument('rev', help='Revision to land')
    @CommandArgument('destination', help='Destination tree for the revision')
    @CommandArgument('pingback_url', default='http://localhost/',
                     help='URL to which Autoland should post result')
    @CommandArgument('--trysyntax', required=False, default='', help='Name of queue to create')
    @CommandArgument('--user', required=False, default='autoland', help='Autoland user')
    @CommandArgument('--password', required=False, default='autoland', help='Autoland password')
    def post_autoland_job(self, host, tree, rev, destination, pingback_url,
                          trysyntax=None, user=None, password=None):
        data = {
            'tree': tree,
            'rev': rev,
            'destination': destination,
            'trysyntax': trysyntax,
            'pingback_url': pingback_url
        }

        r = requests.post(host + '/autoland', data=json.dumps(data),
                          headers={'Content-Type': 'application/json'},
                          auth=(user, password))
        print(r.status_code, r.text)

    @Command('autoland-job-status', category='autoland',
        description='Get an autoland job status')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('requestid', help='Id of the job for which to get status')
    def autoland_job_status(self, host, requestid):
        r = requests.get(host + '/autoland/status/' + requestid)
        print(r.status_code, r.text)
