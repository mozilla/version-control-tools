# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


class FileDiffReviewerTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com',
                             b'mjane', 2001, b'Mary Jane')

            bb = self.user_bugzilla('mjane@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test try;r=jsmith'])
            lr.run(['push'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_filediffreviewer_buttons(self):
        """Clicking on the review status should change its text and class"""

        self.reviewboard_login('jsmith@example.com', 'password1')
        self.load_rburl('r/1/diff/1/')

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'diff-file-btn')))

        review_button = self.browser.find_element_by_class_name(
            'diff-file-btn')
        self.assertEqual(review_button.text, 'not reviewed')
        self.assertEqual(review_button.get_attribute('class'),
                         'diff-file-btn')

        # clicking on the button should switch to `reviewed`
        review_button.click()
        WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, 'diff-file-btn')))

        self.assertEqual(review_button.text, 'reviewed')
        self.assertEqual(review_button.get_attribute('class'),
                         'diff-file-btn reviewed')

        # another click should switch it back to `not reviewed`
        review_button.click()
        WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, 'diff-file-btn')))

        self.assertEqual(review_button.text, 'not reviewed')
        self.assertEqual(review_button.get_attribute('class'),
                         'diff-file-btn')
