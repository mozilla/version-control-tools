# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


class ReviewerSpecificationTest(MozReviewWebDriverTest):
    def test_reviewer_specification(self):
        # This tests whether or not it's possible to specify a review in the
        # commit summary and have it appear in the UI and be publishable.
        # Some validation occurs in the UI so it is possible to break
        # publishing but have it appear to work in other tests.
        self.create_users([
            ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
            ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')
        mjb = self.user_bugzilla('mjane@example.com')
        mjb.create_bug('TestProduct', 'TestComponent', 'bug1')

        lr = self.create_basic_repo('mjane@example.com', 'mjane')
        lr.write('foo', 'first change\n')
        lr.run(['commit', '-m',
                'Bug 1 - Test reviewer specification; r=jsmith'])
        lr.run(['push'])

        self.reviewboard_login('mjane@example.com', 'password2')

        self.load_rburl('r/1')

        WebDriverWait(self.browser, 3).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'mozreview-child-reviewer-list'), 'jsmith'))

        reviewers = self.browser.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0].text, 'jsmith')
