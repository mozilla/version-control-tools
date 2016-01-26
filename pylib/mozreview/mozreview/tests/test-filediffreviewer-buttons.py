# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
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
                ('jdoe@example.com', 'password3', 'John Doe [:jdoe]'),
            ])

            self.create_ldap(b'mjane@example.com',
                             b'mjane', 2001, b'Mary Jane')

            bb = self.user_bugzilla('mjane@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test try;r=jsmith'])
            lr.run(['push'])
            lr.write('foo', 'second change')
            lr.run(['commit', '-m', 'second change;r=jsmith'])
            lr.run(['push'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def _element_is_present(self, selector, timeout=10):
        try:
            WebDriverWait(self.browser, timeout).until(
                EC.presence_of_element_located(selector))
            return True
        except TimeoutException:
            return False

    def test_filediffreviewer_buttons(self):
        """Clicking on the review status should change its text and class"""

        self.reviewboard_login('jdoe@example.com', 'password3')
        self.load_rburl('r/1/diff/1/')

        self.assertTrue(
            self._element_is_present((By.CLASS_NAME, 'diff-file-btn'))
        )

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

        left_revision_selector = self.browser.find_elements_by_class_name(
            'revision-selector-handle')[0]
        right_revision_selector = self.browser.find_elements_by_class_name(
            'revision-selector-handle')[1]

        first_revision = self.browser.find_elements_by_class_name(
            'revision-selector-tick')[1]
        last_revision = self.browser.find_elements_by_class_name(
            'revision-selector-tick')[2]

        action_chains = ActionChains(self.browser)
        action_chains.drag_and_drop(right_revision_selector,
                                    first_revision).perform()

        WebDriverWait(self.browser, 10).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#diff_revision_label h1'),
                'Diff Revision 1'
            )
        )

        self.assertTrue(
            self._element_is_present((By.CLASS_NAME, 'diff-file-btn'))
        )

        action_chains.drag_and_drop(right_revision_selector,
                                    last_revision).perform()

        action_chains.drag_and_drop(left_revision_selector,
                                    first_revision).perform()

        WebDriverWait(self.browser, 10).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, '#diff_revision_label h1'),
                'Changes between revision 1 and 2'
            )
        )

        self.assertFalse(
            self._element_is_present((By.CLASS_NAME, 'diff-file-btn'))
        )
