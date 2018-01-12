# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import json
import requests

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

MAX_POLL_ATTEMPTS = 20
POLL_INTERVAL = 0.1


@CommandProvider
class AutolandCommands(object):

    def _poll_autoland_status(self, poll, url):
        if not poll:
            r = requests.get(url)
            print(r.status_code, r.text)
        else:
            import json
            import time
            attempts = 0
            while attempts < MAX_POLL_ATTEMPTS:
                attempts += 1
                r = requests.get(url)
                if r.status_code != 200 or json.loads(r.text)['landed'] is not None:
                    print(r.status_code, r.text)
                    break
                time.sleep(POLL_INTERVAL)
            else:
                print('timed out')

    @Command('post-autoland-job', category='autoland',
             description='Post a job to autoland')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('tree', help='Source tree of the revision')
    @CommandArgument('rev', help='Revision to land')
    @CommandArgument('destination', help='Destination tree for the revision')
    @CommandArgument('pingback_url', default='http://localhost/',
                     help='URL to which Autoland should post result')
    @CommandArgument('--trysyntax', required=False, default='',
                     help='Try syntax to use [optional]')
    @CommandArgument('--push-bookmark', required=False, default='',
                     help='Bookmark name to use when pushing [optional]')
    @CommandArgument('--commit-descriptions', required=False, default='',
                     help='Commit descriptions to use when rewriting [optional]')
    @CommandArgument('--ldap-username', required=False, default='autolanduser@example.com',
                     help='Commit descriptions to use when rewriting [optional]')
    @CommandArgument('--user', required=False, default='autoland',
                     help='Autoland user')
    @CommandArgument('--password', required=False, default='autoland',
                     help='Autoland password')
    @CommandArgument('--patch-url', required=False, default='',
                     help='URL of patch [optional]')
    @CommandArgument('--patch-file', required=False, default='',
                     help='Patch file to inline into request [optional]')
    def post_autoland_job(self, host, tree, rev, destination, pingback_url,
                          trysyntax=None, push_bookmark=None,
                          commit_descriptions=None, ldap_username=None,
                          user=None, password=None, patch_url=None,
                          patch_file=None):

        data = {
            'tree': tree,
            'rev': rev,
            'destination': destination,
            'pingback_url': pingback_url
        }
        if trysyntax:
            data['trysyntax'] = trysyntax
        if push_bookmark:
            data['push_bookmark'] = push_bookmark
        if commit_descriptions:
            data['commit_descriptions'] = json.loads(commit_descriptions)
        if ldap_username:
            data['ldap_username'] = ldap_username
        if patch_url:
            data['patch_urls'] = [patch_url]
        if patch_file:
            with open(patch_file) as f:
                data['patch'] = base64.b64encode(f.read())

        host = host.rstrip('/')
        r = requests.post(host + '/autoland', data=json.dumps(data),
                          headers={'Content-Type': 'application/json'},
                          auth=(user, password))
        print(r.status_code, r.text)

    @Command('autoland-job-status', category='autoland',
        description='Get an autoland job status')
    @CommandArgument('host', help='Host to which to post the job')
    @CommandArgument('requestid', help='Id of the job for which to get status')
    @CommandArgument('--poll', required=False, action='store_true',
                     help='Poll the status until the job is serviced')
    def autoland_job_status(self, host, requestid, poll):
        url = host.rstrip('/') + '/autoland/status/' + requestid
        AutolandCommands._poll_autoland_status(self, poll, url)

    @Command('wait-for-autoland-pingback', category='autoland',
        description='Wait for an autoland job pingback')
    @CommandArgument('host', help='Address on which to listen')
    @CommandArgument('port', type=int, help='Port on which to listen')
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
