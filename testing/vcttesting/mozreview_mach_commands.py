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
class MozReviewCommands(object):
    def _get_mozreview(self, where):
        if not where and 'MOZREVIEW_HOME' in os.environ:
            where = os.environ['MOZREVIEW_HOME']

        from vcttesting.mozreview import MozReview
        return MozReview(where)

    @Command('start', category='mozreview',
        description='Start a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('--bugzilla-port', type=int,
        help='Port Bugzilla HTTP server should listen on.')
    @CommandArgument('--reviewboard-port', type=int,
        help='Port Review Board HTTP server should listen on.')
    @CommandArgument('--mercurial-port', type=int,
        help='Port Mercurial HTTP server should listen on.')
    def start(self, where, bugzilla_port, reviewboard_port,
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
        print('Run the following to use this instance with all future commands:')
        print('  export MOZREVIEW_HOME=%s' % mr._path)

    @Command('stop', category='mozreview',
        description='Stop a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    def stop(self, where):
        mr = self._get_mozreview(where)
        mr.stop()

    @Command('create-repo', category='mozreview',
        description='Add a repository to a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('path', help='Relative path of repository')
    def create_repo(self, where, path):
        mr = self._get_mozreview(where)
        url, rbid = mr.create_repository(path)
        print('URL: %s' % url)

    @Command('create-user', category='mozreview',
        description='Create a user in a MozReview instance')
    @CommandArgument('where', nargs='?',
        help='Directory of MozReview instance')
    @CommandArgument('email', help='Email address for user')
    @CommandArgument('password', help='Password for user')
    @CommandArgument('fullname', help='Full name for user')
    def create_user(self, where, email, password, fullname):
        mr = self._get_mozreview(where)
        u = mr.create_user(email, password, fullname)
        print('Created user %s' % u['id'])
