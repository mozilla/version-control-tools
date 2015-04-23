# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import shutil
import tempfile
import unittest

from selenium import webdriver
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.docker import DockerNotAvailable
from vcttesting.mozreview import MozReview


class MozReviewTest(unittest.TestCase):
    """A base class used for testing MozReview instances.

    When instances of this test class are instantiated, we set up a MozReview
    instance.

    The MozReview instance is available for the lifetime of the test class.
    i.e. it is shared between all test functions.
    """

    @classmethod
    def setUpClass(cls):
        tmpdir = tempfile.mkdtemp()
        cls._tmpdir = tmpdir

        try:
            mr = MozReview(tmpdir)
        except DockerNotAvailable:
            raise unittest.SkipTest('Docker not available')

        cls.mr = mr
        # If this fails mid-operation, we could have some services running.
        # unittest doesn't call tearDownClass if setUpClass fails. So do it
        # ourselves.
        try:
            # The environment variables should be set by the test runner. If
            # they aren't set, you are likely invoking the tests wrong.
            mr.start(db_image=os.environ['DOCKER_BMO_DB_IMAGE'],
                     web_image=os.environ['DOCKER_BMO_WEB_IMAGE'],
                     ldap_image=os.environ['DOCKER_LDAP_IMAGE'],
                     pulse_image=os.environ['DOCKER_PULSE_IMAGE'],
                     autolanddb_image=os.environ['DOCKER_AUTOLANDDB_IMAGE'],
                     autoland_image=os.environ['DOCKER_AUTOLAND_IMAGE'],
                     hgrb_image=os.environ['DOCKER_HGRB_IMAGE'],
                     rbweb_image=os.environ['DOCKER_RBWEB_IMAGE'])
        except Exception:
            mr.stop()
            shutil.rmtree(tmpdir)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.mr.stop()
        shutil.rmtree(cls._tmpdir)

    @property
    def bzurl(self):
        return self.mr.bugzilla_url

    @property
    def rburl(self):
        return self.mr.reviewboard_url

    @property
    def hgurl(self):
        return self.mr.mercurial_url

    def bugzilla(self, **kwargs):
        return self.mr.get_bugzilla(**kwargs)

    @property
    def ldap(self):
        return self.mr.get_ldap()


class MozReviewWebDriverTest(MozReviewTest):
    """A base class used for testing MozReview instances.

    When instances of this test class are instantiated, we set up a MozReview
    instance and prepare the Selenium WebDriver connection to that instance.

    This test thus facilitates the easy testing of web browser interaction with
    MozReview server components.
    """

    @classmethod
    def setUpClass(cls):
        try:
            cls.browser = webdriver.Firefox()
        except Exception:
            raise unittest.SkipTest('Unable to start Firefox')

        # Exceptions during setUpClass don't result in calls to tearDownClass,
        # so do it ourselves.
        try:
            MozReviewTest.setUpClass()
        except Exception:
            cls.browser.quit()
            raise

        cls.users = {}

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        MozReviewTest.tearDownClass()

    def tearDown(self):
        self.browser.delete_all_cookies()
        super(MozReviewWebDriverTest, self).tearDown()

    @property
    def switch_to(self):
        return SwitchTo(self.browser)

    def load_rburl(self, path):
        """Load the specified Review Board URL."""
        self.browser.get('%s%s' % (self.rburl, path))

    def verify_rburl(self, path):
        """Verify the current URL is the specified Review Board URL."""
        current = self.browser.current_url
        self.assertEqual(current, '%s%s' % (self.rburl, path))

    def reviewboard_login(self, username, password, verify=True):
        """Log into Review Board with the specified credentials."""
        self.load_rburl('account/login')

        input_username = self.browser.find_element_by_id('id_username')
        input_username.send_keys(username)
        input_password = self.browser.find_element_by_id('id_password')
        input_password.send_keys(password)

        input_password.submit()

        if verify:
            self.verify_rburl('dashboard/')

    def create_users(self, users):
        """Create multiple users at once.

        Receives an iterable of (email, password, name) 3-tuples.
        """
        b = self.bugzilla(username='admin@example.com', password='password')
        for (email, password, name) in users:
            b.create_user(email, password, name)
            self.users[email] = (password, name)

    def create_ldap(self, email, username, uid, name, scm_level=1):
        kf = os.path.join(self.mr._path, 'keys', email)
        self.ldap.create_user(email, username, uid, name, key_filename=kf,
                              scm_level=scm_level)

    def user_bugzilla(self, email):
        """Obtain a Bugzilla handle for a given user, specified by email address."""
        return self.bugzilla(username=email, password=self.users[email][0])

    def create_basic_repo(self, email, nick):
        self.mr.create_repository('test_repo')
        lr = self.mr.get_local_repository(
            'test_repo',
            ircnick=nick,
            bugzilla_username=email,
            bugzilla_password=self.users[email][0])
        lr.touch('foo')
        lr.run(['commit', '-A', '-m', 'initial'])
        lr.run(['phase', '--public', '-r', '0'])

        return lr

    def wait_for_reviewers_to_load(self):
        """Wait for reviewers information to load."""
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'child-rr-reviewers')))

    def get_commits_el(self):
        """Obtain the element containing the multi-commit information."""
        return self.browser.find_element_by_id('mozreview-commits')

    def prepare_edit_reviewers(self, idx):
        """Start editing reviewers for the commit at index ``idx``."""
        commits = self.get_commits_el()
        editicons = commits.find_elements_by_class_name('editicon')
        icon = editicons[idx]
        icon.click()

        autocompletes = commits.find_elements_by_class_name('ui-autocomplete-input')
        self.assertEqual(len(autocompletes), 1)
        return autocompletes[0]

    def wait_for_autocomplete_results(self):
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, 'ui-autocomplete-results')))
        results = self.browser.find_elements_by_class_name('ui-autocomplete-results')
        self.assertEqual(len(results), 1)
        return results[0]
