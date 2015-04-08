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

        host = host.rstrip('/')
        r = requests.post(host + '/autoland', data=json.dumps(data),
                          headers={'Content-Type': 'application/json'},
                          auth=(user, password))
        print(r.status_code, r.text)

    @Command('autoland-job-status', category='autoland',
        description='Get an autoland job status')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('requestid', help='Id of the job for which to get status')
    def autoland_job_status(self, host, requestid):
        host = host.rstrip('/')
        r = requests.get(host + '/autoland/status/' + requestid)
        print(r.status_code, r.text)

    @Command('wait-for-autoland-pingback', category='autoland',
        description='Wait for an autoland job pingback')
    @CommandArgument('host', help='Address on which to listen')
    @CommandArgument('port', type=int, help='Port oo which to listen')
    @CommandArgument('timeout', type=int, help='Timeout')
    def wait_for_autoland_pingback(self, host, port, timeout):
        import SocketServer

        class AutolandServer(SocketServer.TCPServer):
            def handle_timeout(self):
                print('timed out')

        class RequestHandler(SocketServer.BaseRequestHandler):
            def handle(self):
                self.data = self.request.recv(4096).split('\n')
                self.request.sendall('HTTP/1.1 200 OK\r\n')

                # this outputs just the request body
                print(self.data[-1].strip())

        server = AutolandServer((host, port), RequestHandler)
        server.allow_reuse_address = True
        server.timeout = timeout
        server.handle_request()

    @Command('post-pullrequest-job', category='autoland',
        description='Post a pullrequest job to autoland')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('ghuser', help='Github user of the pullrequest')
    @CommandArgument('repo', help='Github repository of the pullrequest')
    @CommandArgument('pullrequest', help='Pull request identifier')
    @CommandArgument('destination', help='Destination tree for the revision')
    @CommandArgument('bzuserid', help='Bugzilla userid for authentication')
    @CommandArgument('bzcookie', help='Bugzilla cookie for authentication')
    @CommandArgument('bugid', help='Bugzilla cookie for authentication')
    @CommandArgument('pingback_url', default='http://localhost/',
                     help='URL to which Autoland should post result')
    @CommandArgument('--user', required=False, default='autoland', help='Autoland user')
    @CommandArgument('--password', required=False, default='autoland', help='Autoland password')
    def post_pullrequest_job(self, host, ghuser, repo, pullrequest, destination,
                             bzuserid, bzcookie, bugid, pingback_url,
                             user=None, password=None):
        data = {
            'user': ghuser,
            'repo': repo,
            'pullrequest': pullrequest,
            'destination': destination,
            'bzuserid': bzuserid,
            'bzcookie': bzcookie,
            'bugid': bugid,
            'pingback_url': pingback_url
        }

        r = requests.post(host + '/pullrequest/mozreview', data=json.dumps(data),
                          headers={'Content-Type': 'application/json'},
                          auth=(user, password))
        print(r.status_code, r.text)

    @Command('pullrequest-job-status', category='autoland',
        description='Get an autoland job status')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('requestid', help='Id of the job for which to get status')
    def pullrequest_job_status(self, host, requestid):
        r = requests.get(host + '/pullrequest/mozreview/status/' + requestid)
        print(r.status_code, r.text)
