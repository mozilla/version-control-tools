# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import socket

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)

@CommandProvider
class ServerCommands(object):
    def __init__(self, context):
        self.context = context

    def _get_mozreview(self, where):
        from vcttesting.mozreview import MozReview
        return MozReview(where)

    @Command('mozreview-start', category='mozreview',
        description='Start a MozReview instance')
    @CommandArgument('where', help='Directory for data')
    @CommandArgument('--bugzilla-port', type=int,
        help='Port Bugzilla HTTP server should listen on.')
    @CommandArgument('--reviewboard-port', type=int,
        help='Port Review Board HTTP server should listen on.')
    @CommandArgument('--mercurial_port', type=int,
        help='Port Mercurial HTTP server should listen on.')
    def mozreview_start(self, where, bugzilla_port, reviewboard_port,
            mercurial_port):
        mr = self._get_mozreview(where)
        mr.start(bugzilla_port=bugzilla_port,
                reviewboard_port=reviewboard_port,
                mercurial_port=mercurial_port,
                verbose=True)

        print('Bugzilla URL: %s' % mr.bugzilla_url)
        print('Review Board URL: %s' % mr.reviewboard_url)
        print('Mercurial URL: %s' % mr.mercurial_url)
        print('Admin username: %s' % mr.admin_username)
        print('Admin password: %s' % mr.admin_password)

    @Command('mozreview-stop', category='mozreview',
        description='Stop a MozReview instance')
    @CommandArgument('where', help='Directory of MozReview instance')
    def mozreview_stop(self, where):
        mr = self._get_mozreview(where)
        mr.stop()

    @Command('mozreview-create-repo', category='mozreview',
        description='Add a repository to a MozReview instance')
    @CommandArgument('where', help='Directory of MozReview instance')
    @CommandArgument('path', help='Relative path of repository')
    def mozreview_create_repo(self, where, path):
        mr = self._get_mozreview(where)
        url, rbid = mr.create_repository(path)
        print('URL: %s' % url)

    @Command('mozreview-create-user', category='mozreview',
        description='Create a user in a MozReview instance')
    @CommandArgument('where', help='Directory of MozReview instance')
    @CommandArgument('email', help='Email address for user')
    @CommandArgument('password', help='Password for user')
    @CommandArgument('fullname', help='Full name for user')
    def mozreview_create_user(self, where, email, password, fullname):
        mr = self._get_mozreview(where)
        u = mr.create_user(email, password, fullname)
        print('Created user %s' % u['id'])
