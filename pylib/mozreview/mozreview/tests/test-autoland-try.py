# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest

class AutolandTryTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')

            bb = self.user_bugzilla('mjane@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test try'])
            lr.run(['push'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_autoland_try(self):
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')

        # We should not be able to trigger a Try run until the review is
        # published.
        # TODO: actually test this
        self.assign_reviewer(0, 'jsmith')
        publish_btn = self.browser.find_element_by_id('btn-draft-publish')
        publish_btn.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        automation_menu = self.browser.find_element_by_id('automation-menu')
        automation_menu.click()
        try_btn = self.browser.find_element_by_id('autoland-try-trigger')

        # Clicking the button should display a trychooser dialog
        try_btn.click()
        try_text = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID,
            'mozreview-autoland-try-syntax')))
        try_text.send_keys('try: stuff')
        try_submit = self.browser.find_element_by_xpath('//input[@value="Submit"]')

        # clicking the Submit button should display an activity indicator
        try_submit.click()

        element = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, 'activity-indicator'))
        )
        try:
            self.assertTrue('A server error occurred' not in element.text)
        except StaleElementReferenceException:
            # The activity indicator may already have disappeared by the time
            # we check the text, but we want to be able to catch the server
            # error if it shows up.
            pass

        # the try job should eventually create a new change description
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'changedesc'))
        )

        time.sleep(5)
        self.browser.refresh()
        changedesc = self.browser.find_element_by_class_name('changedesc')
        iframe = changedesc.find_element_by_tag_name('iframe')
        self.assertTrue('https://treeherder.mozilla.org/'
            in iframe.get_attribute('src'))

        # We should not be able to trigger a Try run for another user.
        self.reviewboard_login('jsmith@example.com', 'password1')
        self.load_rburl('r/1')
        with self.assertRaises(NoSuchElementException):
            self.browser.find_element_by_id('mozreview-autoland-try-trigger')
