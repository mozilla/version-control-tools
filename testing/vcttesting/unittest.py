# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from urllib import urlencode

from selenium import webdriver
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.docker import DockerNotAvailable
from vcttesting.mozreview import MozReview


# The environment variables should be set by the test runner. If
# they aren't set, you are likely invoking the tests wrong.
def start_mozreview(mr):
    mr.start(db_image=os.environ['DOCKER_BMO_DB_IMAGE'],
         web_image=os.environ['DOCKER_BMO_WEB_IMAGE'],
         ldap_image=os.environ['DOCKER_LDAP_IMAGE'],
         pulse_image=os.environ['DOCKER_PULSE_IMAGE'],
         autolanddb_image=os.environ['DOCKER_AUTOLANDDB_IMAGE'],
         autoland_image=os.environ['DOCKER_AUTOLAND_IMAGE'],
         hgrb_image=os.environ['DOCKER_HGRB_IMAGE'],
         rbweb_image=os.environ['DOCKER_RBWEB_IMAGE'],
         hgweb_image=os.environ['DOCKER_HGWEB_IMAGE'])


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
            start_mozreview(mr)
        except Exception:
            mr.stop()
            shutil.rmtree(tmpdir)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.mr.stop()
        shutil.rmtree(cls._tmpdir)

    def run(self, *args, **kwargs):
        """Wrap run to enable restart between tests mode."""
        if getattr(self, '_restart_between_tests', False):
            self.addCleanup(self.mr.stop)
            # setUpClass always starts.
            if not self.mr.started:
                start_mozreview(self.mr)

        return super(MozReviewTest, self).run(*args, **kwargs)

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
        if 'ONLY_HEADLESS_TESTS' in os.environ:
            raise unittest.SkipTest('Only running headless tests')

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

    def load_bzurl(self, path):
        """Load the specified Bugzilla URL."""
        self.browser.get('%s%s' % (self.bzurl, path))

    def verify_rburl(self, path):
        """Verify the current URL is the specified Review Board URL."""
        current = self.browser.current_url
        self.assertEqual(current, '%s%s' % (self.rburl, path))

    def verify_bzurl(self, path):
        """Verify the current URL is the specified Bugzilla URL."""
        current = self.browser.current_url
        self.assertEqual(current, '%s%s' % (self.bzurl, path))

    def reviewboard_login(self, username, password, verify=True):
        """Log into Review Board with the specified credentials."""
        # Ensure that we're logged out of both Review Board and Bugzilla;
        # otherwise we will be automatically logged back in.
        self.load_rburl('mozreview/logout/')
        self.load_bzurl('index.cgi?logout=1')
        self.load_rburl('account/login/')

        # Wait for redirect to Bugzilla login.
        bz_auth_url_path = 'auth.cgi?%s' % urlencode({
            'callback': '%smozreview/bmo_auth_callback/' % self.rburl,
            'description': 'mozreview'
        })
        bz_auth_url = '%s%s' % (self.bzurl, bz_auth_url_path)

        for _ in xrange(0, 5):
            if self.browser.current_url == bz_auth_url:
                break
            time.sleep(1)

        self.verify_bzurl(bz_auth_url_path)

        input_username = self.browser.find_element_by_id('Bugzilla_login')
        input_username.send_keys(username)
        input_password = self.browser.find_element_by_id('Bugzilla_password')
        input_password.send_keys(password)

        input_password.submit()

        if verify:
            WebDriverWait(self.browser, 10).until(
                EC.title_is(u'My Dashboard | Review Board'))

    def create_users(self, users):
        """Create multiple users at once.

        Receives an iterable of (email, password, name) 3-tuples.
        """
        b = self.bugzilla(username='admin@example.com', password='password')
        for (email, password, name) in users:
            b.create_user(email, password, name)
            api_key = self.mr.create_user_api_key(email)
            self.users[email] = (password, name, api_key)

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
            bugzilla_apikey=self.users[email][2])
        lr.touch('foo')
        lr.run(['commit', '-A', '-m', 'initial'])
        lr.run(['phase', '--public', '-r', '0'])

        return lr

    def wait_for_reviewers_to_load(self):
        """Wait for reviewers information to load."""
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list')))

    def get_commits_el(self):
        """Obtain the element containing the multi-commit information."""
        return self.browser.find_element_by_id('mozreview-child-requests')

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

    def assign_reviewer(self, commit_index, reviewer):
        children = self.browser.find_element_by_id('mozreview-child-requests')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list')))
        editicons = children.find_elements_by_class_name('editicon')

        editicons[commit_index].click()

        autocomplete = children.find_elements_by_class_name('ui-autocomplete-input')
        autocomplete = autocomplete[commit_index]

        autocomplete.send_keys(reviewer)

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'ui-autocomplete-results')))
        results = self.browser.find_elements_by_class_name('ui-autocomplete-results')
        self.assertEqual(len(results), 1)

        # If you comment this out and press ENTER from the browser, you
        # get an error. It works from Selenium. Strange.
        autocomplete.send_keys(Keys.ENTER)

    def dump_autoland_log(self):
        subprocess.call('docker exec %s cat /home/ubuntu/autoland.log' %
                        self.mr.autoland_id, shell=True)

    def dump_reviewboard_log(self):
        """Dump the reviewboard log to stdout to help debug failing tests"""

        subprocess.call('docker exec %s cat /reviewboard/logs/reviewboard.log' %
                        self.mr.rbweb_id, shell=True)

    def add_hostingservice(self, repo, account_username, required_ldap_group,
                           try_repository_url):
        """This adds a hosting service to an existing account"""

        self.reviewboard_login('admin@example.com', 'password')
        self.load_rburl('/admin/db/scmtools/repository/%s/' % repo)

        el = self.browser.find_element_by_id('id_path')
        path = el.get_attribute('value')

        select = Select(self.browser.find_element_by_id('id_hosting_type'))
        select.select_by_visible_text('hmo')

        # If the account exists (i.e. another test ran first), this will fail.
        try:
            el = self.browser.find_element_by_id('id_hosting_account_username')
            el.send_keys(account_username)
        except ElementNotVisibleException:
            pass

        el = self.browser.find_element_by_id('id_repository_url')
        el.send_keys(path)

        el = self.browser.find_element_by_id('id_try_repository_url')
        el.send_keys(try_repository_url)

        el = self.browser.find_element_by_id('id_required_ldap_group')
        for c in el.get_attribute('value'):
            el.send_keys(Keys.BACKSPACE)
        el.send_keys(required_ldap_group)

        el.send_keys(Keys.RETURN)

        # If this succeeds, we should be redirected to the repositories page
        WebDriverWait(self.browser, 10).until(
            lambda x: 'Select repository to change' in self.browser.title)


def restart_between_tests(cls):
    """A class decorator for MozReviewTest that will restart the cluster.

    Default behavior for MozReviewTest is to start the cluster and keep it
    running until all tests have executed.

    Some tests may wish to have fresh cluster instances for each test method
    in the test class. Adding this decorator causes the cluster to restart
    after each test and gives each test method a clean slate.

    This execution method does add overhead. So considered reusing clusters
    when possible.
    """
    setattr(cls, '_restart_between_tests', True)
    return cls
