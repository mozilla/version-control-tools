# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


class BrowserCacheTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('user1@example.com', 'password', 'User One [:user1]'),
                ('user2@example.com', 'password', 'User Two [:user2]'),
            ])

            self.create_ldap(b'user1@example.com', b'user1', 2001, b'User One')

            bb = self.user_bugzilla('user1@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('user1@example.com', 'user1')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Commit 1. r?user2'])
            lr.write('foo', 'second change')
            lr.run(['commit', '-m', 'Bug 1 - Commit 2. r?user2'])
            lr.run(['push', '--config', 'reviewboard.autopublish=true'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_browser_cache(self):
        """Test that browser caching is properly invalidated"""
        self.reviewboard_login('user1@example.com', 'password')

        # Prime the browser cache.
        self.load_rburl('r/1')
        self.load_rburl('r/2')
        self.load_rburl('r/3')

        # Make a review to change the commit's status.
        self.load_rburl('r/3/diff/')

        ln = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "id('chunk0.0')/tr[1]/th[1]"
            )))

        ActionChains(self.browser).move_to_element(ln).click(ln).perform()

        time.sleep(1)  # Give time for the comment box to become focused
        ActionChains(self.browser).send_keys("Comment!").perform()

        save = self.browser.find_element_by_xpath(
            "//div[@class='comment-dlg-footer']/div[@class='buttons']/"
            "input[@class='save']")
        save.click()

        finish_btn = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "id('review-banner-edit')"
            )))
        finish_btn.click()

        publish_btn = WebDriverWait(self.browser, 5).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "id('review-form-modalbox')/div[1]/div[2]/input[1]"
            )))
        publish_btn.click()

        # Wait until we've been redirected to the reviews page
        WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((
                By.XPATH, "id('issue-summary')")))

        # The Commit Table should show an issue count for the current
        # review requests status.
        status_el = self.get_commit_status(2)
        self.assertEqual(status_el.get_attribute('class'), 'issue-count')

        self.load_rburl('r/2')
        # The Commit Table shouldn't show a stale status for the second
        # commit even though no operations have been performed on the
        # first commit's review request.
        status_el = self.get_commit_status(2)
        self.assertEqual(status_el.get_attribute('class'), 'issue-count')

    def get_commit_status(self, i):
        return WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//table[@id='mozreview-child-requests']"
                "/tbody/tr[%s]/td[@class='status']/*[1]" % i
            )))
