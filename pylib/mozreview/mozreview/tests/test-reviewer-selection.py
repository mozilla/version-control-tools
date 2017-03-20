# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time
import unittest

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


@unittest.skip('Skipped due to Bug 1348725')
class AutocompleteTest(MozReviewWebDriverTest):
    def test_reviewer_autocomplete(self):
        self.create_users([
            ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
            ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')
        mjb = self.user_bugzilla('mjane@example.com')
        mjb.create_bug('TestProduct', 'TestComponent', 'bug1')

        lr = self.create_basic_repo('mjane@example.com', 'mjane')
        lr.write('foo', 'first change\n')
        lr.run(['commit', '-m', 'Bug 1 - Test autocomplete'])
        lr.write('foo', 'second change\n')
        lr.run(['commit', '-m', 'This is the second commit'])
        lr.run(['push', '--config', 'reviewboard.autopublish=false'])

        self.reviewboard_login('mjane@example.com', 'password2')

        self.load_rburl('r/1')

        # assign a reviewer to the first commit
        self.assign_reviewer(0, 'jsmith')

        time.sleep(1)
        publish = self.browser.find_element_by_id('btn-draft-publish')
        publish.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list')))
        reviewers = self.browser.find_elements_by_class_name('mozreview-child-reviewer-list')
        self.assertEqual(len(reviewers), 2)
        self.assertEqual(reviewers[0].text, 'jsmith')
        self.assertEqual(reviewers[1].text, '')

        # Here we test that adding the same reviewer to a different commit
        # works as expected.
        children = self.browser.find_element_by_id('mozreview-child-requests')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list')))

        self.assign_reviewer(1, 'jsmith')

        time.sleep(1)
        publish = self.browser.find_element_by_id('btn-draft-publish')
        publish.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list')))
        reviewers = self.browser.find_elements_by_class_name('mozreview-child-reviewer-list')

        self.assertEqual(len(reviewers), 2)
        self.assertEqual(reviewers[0].text, 'jsmith')
        self.assertEqual(reviewers[1].text, 'jsmith')
