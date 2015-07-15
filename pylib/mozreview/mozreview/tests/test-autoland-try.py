# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest
import time

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest

@unittest.skip("disabled until bug 1180818 is fixed")
class AutolandTryTest(MozReviewWebDriverTest):
    def test_autoland_try(self):
        self.create_users([
            ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
            ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')
        mjb = self.user_bugzilla('mjane@example.com')
        mjb.create_bug('TestProduct', 'TestComponent', 'bug1')

        lr = self.create_basic_repo('mjane@example.com', 'mjane')
        lr.write('foo', 'first change\n')
        lr.run(['commit', '-m', 'Bug 1 - Test try; r=mary'])
        lr.run(['push'])

        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')

        # We should not be able to trigger a Try run until the review is
        # published.
        try_btn = self.browser.find_element_by_id('mozreview-autoland-try-trigger')
        self.assertFalse(try_btn.is_enabled())
        publish_btn = self.browser.find_element_by_id('btn-draft-publish')
        publish_btn.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        try_btn = self.browser.find_element_by_id('mozreview-autoland-try-trigger')
        self.assertTrue(try_btn.is_enabled())

        # We should not be able to trigger a Try run for another user.
        self.reviewboard_login('jsmith@example.com', 'password1')
        self.load_rburl('r/1')
        try_btn = self.browser.find_element_by_id('mozreview-autoland-try-trigger')
        self.assertFalse(try_btn.is_enabled())
