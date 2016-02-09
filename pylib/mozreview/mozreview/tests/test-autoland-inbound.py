# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import absolute_import, unicode_literals

import os
import time

from rbtools.api.client import RBClient
from rbtools.api.transport.sync import SyncTransport

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


class AutolandInboundTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com', b'mjane', 2001,
                             b'Mary Jane', scm_level=3)

            bb = self.user_bugzilla('mjane@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test try'])
            lr.run(['push'])

            self.mr.create_repository('inbound_test_repo')

        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def ship_it(self, rrid, username, password):
        """Create and publish a ship-it review"""

        # TODO: this code is lifted from the reviewboard mach commands. If we
        #       need to make more reviewboard api calls in these tests, we
        #       should make a function in the base class to get a RBClient.
        class NoCacheTransport(SyncTransport):
            """API transport with disabled caching."""
            def enable_cache(self):
                pass

        # RBClient is persisting login cookies from call to call
        # in $HOME/.rbtools-cookies. We want to be able to easily switch
        # between users, so we clear that cookie between calls to the
        # server and reauthenticate every time.
        try:
            os.remove(os.path.join(os.environ.get('HOME'), '.rbtools-cookies'))
        except Exception:
            pass

        client = RBClient(self.rburl, username=username,
                          password=password, transport_cls=NoCacheTransport)
        root = client.get_root()

        reviews = root.get_reviews(review_request_id=rrid)
        reviews.create(public=True, ship_it=True)

    def test_autoland_inbound(self):
        # We should not be able to land to inbound without a HostingService
        # with an associated inbound repository.
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')
        autoland_btn = self.browser.find_element_by_id('autoland-trigger')
        self.assertEqual(
            autoland_btn.value_of_css_property('opacity'), '0.5')
        self.add_hostingservice(1, 'Sirius Black', 'scm_level_1',
                                'try',
                                'inbound', '')

        # We should also not be able to land to inbound unless the review is
        # published.
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')
        autoland_btn = self.browser.find_element_by_id('autoland-trigger')
        self.assertEqual(
            autoland_btn.value_of_css_property('opacity'), '0.5')
        self.assign_reviewer(0, 'jsmith')
        publish_btn = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, 'btn-draft-publish')))
        publish_btn.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        # We should also not be able to land to inbound unless ship-it has
        # been granted.
        autoland_btn = self.browser.find_element_by_id('autoland-trigger')
        self.assertEqual(
            autoland_btn.value_of_css_property('opacity'), '0.5')

        self.ship_it(2, 'mjane@example.com', 'password2')
        self.load_rburl('r/1')

        automation_menu = self.browser.find_element_by_id('automation-menu')
        automation_menu.click()
        autoland_btn = self.browser.find_element_by_id('autoland-trigger')
        self.assertEqual(
            autoland_btn.value_of_css_property('opacity'), '1')

        # Clicking the button should display the autoland dialog
        autoland_btn.click()

        # Wait for commit rewrite response, which enables the submit btn
        autoland_submit_btn = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.ID, 'autoland-submit'))
        )
        autoland_submit_btn.click()

        # autoland submission triggers a browser refresh, wait for that
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'action-info'))
        )

        # Wait for autoland to process the request
        loading = True
        iteration = 0
        while loading and iteration < 10:
            action_info = WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'action-info')
                )
            )
            loading = action_info.get_attribute('innerHTML').find(
                'Waiting for the Autoland request') != -1
            if loading:
                time.sleep(1)
                self.browser.refresh()
                iteration += 1
        self.assertFalse(loading)

        # We should have closed the review request automatically
        submitted_banner = self.browser.find_element_by_id('submitted-banner')
        self.assertTrue('This change has been marked as submitted.' in
                        submitted_banner.get_attribute('innerHTML'))

        # We should not be able to autoland from a closed review request
        try_btn = self.browser.find_element_by_id('autoland-try-trigger')
        self.assertEqual(
            try_btn.value_of_css_property('opacity'), '0.5')
        autoland_btn = self.browser.find_element_by_id('autoland-trigger')
        self.assertEqual(
            autoland_btn.value_of_css_property('opacity'), '0.5')
