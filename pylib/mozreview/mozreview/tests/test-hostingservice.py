# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from selenium.common.exceptions import ElementNotVisibleException

import selenium.webdriver.support.expected_conditions as EC

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


class HostingServiceTest(MozReviewWebDriverTest):

    def test_add_hostingservice(self):
        self.create_users([
            ('mjane@example.com', 'password', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')
        lr = self.create_basic_repo('mjane@example.com', 'mjane')

        self.reviewboard_login('admin@example.com', 'password')
        self.load_rburl('/admin/db/scmtools/repository/1/')

        select = Select(self.browser.find_element_by_id('id_hosting_type'))
        select.select_by_visible_text('hmo')

        # If the account exists (i.e. another test ran first), this will fail
        try:
            el = self.browser.find_element_by_id('id_hosting_account_username')
            el.send_keys('Sirius Black')
        except ElementNotVisibleException:
            pass

        el = self.browser.find_element_by_id('id_repository_url')
        el.send_keys('https://added-repo.example.com')

        el = self.browser.find_element_by_id('id_try_repository_url')
        el.send_keys('https://added-try-repo.example.com')

        el.send_keys(Keys.RETURN)

        # If this succeeds, we should be redirected to the repositories page
        WebDriverWait(self.browser, 10).until(
            lambda x: 'Select repository to change' in self.browser.title)

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

        el = self.browser.find_element_by_id('id_try_repository_url')
        el.send_keys('https://new-try-repo.example.com')

        el = self.browser.find_element_by_id('id_required_ldap_group')
        el.send_keys(Keys.BACKSPACE)
        el.send_keys('1')

        el.send_keys(Keys.RETURN)

        # If this succeeds, we should be redirected to the repositories page
        WebDriverWait(self.browser, 10).until(
            lambda x: 'Select repository to change' in self.browser.title)
