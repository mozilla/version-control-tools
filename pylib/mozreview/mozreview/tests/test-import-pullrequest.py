# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest

@unittest.skip('importing pull requests not supported')
class ImportPullrequestTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_import_pullrequest(self):
        self.reviewboard_login('mjane@example.com', 'password2')

        self.load_rburl('import-pullrequest/dminor/gecko-dev/1')

        btn = self.browser.find_element_by_id('mozreview-import-pullrequest-trigger');
        btn.click()

        # Clicking the button should display the activity indicator
        element = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, "activity-indicator"))
        )
        try:
            self.assertTrue('Error' not in element.text)
        except StaleElementReferenceException:
            # The activity indicator may already have disappeared by the time
            # we check the text, but we want to be able to catch the error
            # if it shows up.
            pass

        # If this succeeds, we should be redirected to a review for the pull
        # request.
        WebDriverWait(self.browser, 10).until(
            lambda x: 'bz://1/' in self.browser.title)

        # Autoland should create the bug for us.
        bug = self.bugzilla().client.get(1)
        self.assertTrue('A pullrequest' in bug.summary)

        # It is possible to import a pull request again.
        self.load_rburl('import-pullrequest/dminor/gecko-dev/1')

        btn = self.browser.find_element_by_id('mozreview-import-pullrequest-trigger');
        btn.click()

        WebDriverWait(self.browser, 10).until(
            lambda x: 'bz://1/' in self.browser.title)

        # Autoland should reuse the existing bug for this pull request.
        with self.assertRaises(KeyError):
            self.bugzilla().client.get(2)
