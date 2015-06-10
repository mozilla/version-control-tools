# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import shutil
import tempfile

from contextlib import contextmanager

from rbtools.api.client import RBClient


logger = logging.getLogger(__name__)


@contextmanager
def ReviewBoardClient(url, username, password):
    tempd = tempfile.mkdtemp()
    try:
        cookie_file = os.path.join(tempd, 'cookies')
        rbclient = RBClient(url, cookie_file=cookie_file,
                            username=username, password=password)
        yield rbclient
    finally:
        shutil.rmtree(tempd)


class MozReviewBoard(object):
    """Interact with a Mozilla-flavored Review Board install."""

    def __init__(self, docker, cid, url, bugzilla_url=None,
                 pulse_host=None, pulse_port=None,
                 pulse_user='guest', pulse_password='guest'):
        self._docker = docker
        self._cid = cid
        self.url = url
        self.bugzilla_url = bugzilla_url
        self.pulse_host = pulse_host
        self.pulse_port = pulse_port
        self.pulse_user = pulse_user
        self.pulse_password = pulse_password

    def login_user(self, username, password):
        """Log in the specified user to Review Board."""
        with ReviewBoardClient(self.url, username, password) as c:
            c.get_root()

    def add_repository(self, name, url, bugzilla_url):
        """Add a repository to Review Board."""
        bugzilla_url = bugzilla_url.rstrip('/')
        bug_url = '%s/show_bug.cgi?id=%%s' % bugzilla_url

        with ReviewBoardClient(self.url, 'admin@example.com', 'password') as c:
            root = c.get_root()
            repos = root.get_repositories()
            repo = repos.create(name=name, path=url, tool='Mercurial',
                                bug_tracker=bug_url)

            return repo.id

    def make_admin(self, email):
        """Make the user with the specified email an admin.

        This grants superuser and staff privileges to the user.
        """
        self._docker.client.execute(self._cid, ['/make-admin', email])
        logger.info('made %s an admin' % email)

    def create_local_user(self, username, email, password):
        """Make a Review Board user using RBs internal auth."""
        self._docker.client.execute(self._cid, [
            '/create-local-user',
            username,
            email,
            password
        ])
        logger.info('Create local user %s' % username)

    def grant_permission(self, username, permission):
        """Grant a user a Review Board permission."""
        self._docker.client.execute(self._cid, [
            '/grant-permission',
            username,
            permission
        ])
        logger.info('Granted %s the %s permission' % (username, permission))

    def get_profile_data(self, username):
        """Obtain profile fields from a username.

        This essentially returns a dict mapping columns in the accounts_profile
        table to their values.
        """
        res = self._docker.client.execute(self._cid,
                                          ['/dump-profile', username])

        return json.loads(res)
