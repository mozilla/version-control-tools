# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


@unittest.skip('Skipped due to Bug 1348725')
class FileDiffReviewerDraftTest(MozReviewWebDriverTest):
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
            lr.run(['push', '--config', 'reviewboard.autopublish=false'])
            lr.write('foo', 'second change')
            lr.run(['commit', '-m', 'second change;r=jsmith'])
            lr.run(['push', '--config', 'reviewboard.autopublish=false'])
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

    def test_filediffreviewer_buttons_on_draft(self):
        """A draft review request shouldn't have a filediff review button"""

        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1/diff/1/')

        self.assertTrue(
            self._element_is_present((By.CLASS_NAME, 'diff-file-btn'))
        )

        self.load_rburl('r/1/')
        self.assign_reviewer(0, 'jdoe')
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.ID, 'draft-banner')))

        self.load_rburl('r/1/diff/1/')

        self.assertFalse(
            self._element_is_present((By.CLASS_NAME, 'diff-file-btn'))
        )
