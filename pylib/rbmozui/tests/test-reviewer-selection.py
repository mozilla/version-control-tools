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


class AutocompleteTest(MozReviewWebDriverTest):
    def test_reviewer_autocomplete(self):
        self.bugzilla().create_user('jsmith@example.com', 'password1',
                                    'Jeremy Smith [:jsmith]')
        self.bugzilla().create_user('mjane@example.com', 'password2',
                                    'Mary Jane [:mary]')

        mjb = self.bugzilla(username='mjane@example.com',
                            password='password2')
        mjb.create_bug('TestProduct', 'TestComponent', 'bug1')

        self.mr.create_repository('repo1')
        lr = self.mr.get_local_repository(
                'repo1',
                ircnick='mary',
                bugzilla_username='mjane@example.com',
                bugzilla_password='password2')

        lr.touch('foo')
        lr.run(['commit', '-A', '-m', 'initial'])
        lr.run(['phase', '--public', '-r', '0'])
        lr.write('foo', 'first change\n')
        lr.run(['commit', '-m', 'Bug 1 - Test autocomplete'])
        lr.run(['push'])

        self.reviewboard_login('mjane@example.com', 'password2')

        self.browser.get('%sr/1' % self.rburl)

        children = self.browser.find_element_by_id('rbmozui-commits-children')
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'child-rr-reviewers')))
        editicons = children.find_elements_by_class_name('editicon')
        self.assertEqual(len(editicons), 1)
        editicons = editicons[0]
        editicons.click()

        autocomplete = children.find_elements_by_class_name('ui-autocomplete-input')
        self.assertEqual(len(autocomplete), 1)
        autocomplete = autocomplete[0]

        autocomplete.send_keys('jsmith')

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'ui-autocomplete-results')))
        results = self.browser.find_elements_by_class_name('ui-autocomplete-results')
        self.assertEqual(len(results), 1)

        # If you comment this out and press ENTER from the browser, you
        # get an error. It works from Selenium. Strange.
        autocomplete.send_keys(Keys.ENTER)

        WebDriverWait(self.browser, 3).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'child-rr-reviewers'), 'jsmith'))

        time.sleep(1)
        publish = self.browser.find_element_by_id('btn-draft-publish')
        publish.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'child-rr-reviewers')))
        reviewers = self.browser.find_elements_by_class_name('child-rr-reviewers')
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0].text, 'jsmith')
