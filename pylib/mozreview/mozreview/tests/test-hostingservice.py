# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest

from selenium.common.exceptions import ElementNotVisibleException

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


@unittest.skip('Skipped due to Bug 1348725')
class HostingServiceTest(MozReviewWebDriverTest):

    def test_add_hostingservice(self):
        self.create_users([
            ('mjane@example.com', 'password', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')
        bb = self.user_bugzilla('mjane@example.com')
        bb.create_bug('TestProduct', 'TestComponent', 'First Bug')
        lr = self.create_basic_repo('mjane@example.com', 'mjane')
        lr.write('foo', 'first change')
        lr.run(['commit', '-m', 'Bug 1 - Test try'])
        lr.run(['push', '--config', 'reviewboard.autopublish=false'])

        self.add_hostingservice(1, 'Sirius Black', 'scm_level_3',
                                True, 'ssh://hg.example.com/try',
                                True, 'ssh://hg.example.com/mainline', '')

        # If we visit the review url, we should be able to find repository
        # information
        self.reviewboard_login('mjane@example.com', 'password')
        self.load_rburl('r/1')

        el = self.browser.find_element_by_id('repository')
        self.assertEqual(el.get_attribute('data-required-ldap-group'),
                         'scm_level_3')
        self.assertEqual(el.get_attribute('data-has-try-repository'),
                         'true')

        # Make sure that diffs work as expected
        lr.write('foo', 'second change')
        lr.run(['commit', '-m', 'Bug 1 - Test try'])
        lr.run(['push', '--config', 'reviewboard.autopublish=false'])

        self.load_rburl('r/3/diff')
        diff_box = self.browser.find_element_by_class_name('diff-box')

        self.assertFalse('There was an error displaying this diff.'
                         in diff_box.text)

    def test_create_hostingservice(self):
        self.reviewboard_login('admin@example.com', 'password')
        self.load_rburl('/admin/db/scmtools/repository/add/')

        el = self.browser.find_element_by_id('id_name')
        el.send_keys('brand new repo')

        select = Select(self.browser.find_element_by_id('id_hosting_type'))
        select.select_by_visible_text('hmo')

        # If the account exists (i.e. another test ran first), this will fail
        try:
            el = self.browser.find_element_by_id('id_hosting_account_username')
            el.send_keys('Sirius Black')
        except ElementNotVisibleException:
            pass

        el = self.browser.find_element_by_id('id_repository_url')
        el.send_keys('https://new-repo.example.com')

        el = self.browser.find_element_by_id('id_autolanding_to_try_enabled')
        el.click()

        el = self.browser.find_element_by_id('id_try_repository_url')
        el.send_keys('https://new-try-repo.example.com')

        el = self.browser.find_element_by_id('id_autolanding_enabled')
        el.click()

        el = self.browser.find_element_by_id('id_landing_repository_url')
        el.send_keys('https://new-landing-repo.example.com')

        el = self.browser.find_element_by_id('id_required_ldap_group')
        el.send_keys(Keys.BACKSPACE)
        el.send_keys('1')

        el.send_keys(Keys.RETURN)

        # If this succeeds, we should be redirected to the repositories page
        WebDriverWait(self.browser, 10).until(
            lambda x: 'Select repository to change' in self.browser.title)
