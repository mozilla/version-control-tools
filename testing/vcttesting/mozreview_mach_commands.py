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

        db_image = os.environ.get('DOCKER_BMO_DB_IMAGE')
        web_image = os.environ.get('DOCKER_BMO_WEB_IMAGE')
        ldap_image = os.environ.get('DOCKER_LDAP_IMAGE')
        pulse_image = os.environ.get('DOCKER_PULSE_IMAGE')
        autolanddb_image = os.environ.get('DOCKER_AUTOLANDDB_IMAGE')
        autoland_image = os.environ.get('DOCKER_AUTOLAND_IMAGE')

        from vcttesting.mozreview import MozReview
        return MozReview(where, db_image=db_image, web_image=web_image,
                         ldap_image=ldap_image, pulse_image=pulse_image,
                         autolanddb_image=autolanddb_image,
                         autoland_image=autoland_image)

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
    @CommandArgument('--pulse-port', type=int,
        help='Port Pulse should listen on.')
    @CommandArgument('--autoland-port', type=int,
        help='Port Autoland should listen on.')
    @CommandArgument('--ldap-port', type=int,
                     help='Port LDAP server should listen on.')
    def start(self, where, bugzilla_port=None, reviewboard_port=None,
            mercurial_port=None, pulse_port=None, autoland_port=None,
            ldap_port=None):
        mr = self._get_mozreview(where)
        mr.start(bugzilla_port=bugzilla_port,
                reviewboard_port=reviewboard_port,
                mercurial_port=mercurial_port,
                pulse_port=pulse_port,
                autoland_port=autoland_port,
                ldap_port=ldap_port,
                verbose=True)

        print('Bugzilla URL: %s' % mr.bugzilla_url)
        print('Review Board URL: %s' % mr.reviewboard_url)
        print('Mercurial URL: %s' % mr.mercurial_url)
        print('Pulse endpoint: %s:%s' % (mr.pulse_host, mr.pulse_port))
        print('Autoland URL: %s' % mr.autoland_url)
        print('Admin username: %s' % mr.admin_username)
        print('Admin password: %s' % mr.admin_password)
        print('LDAP URI: %s' % mr.ldap_uri)
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
