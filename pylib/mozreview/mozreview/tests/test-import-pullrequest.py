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


class ImportPullrequestTest(MozReviewWebDriverTest):
    def test_import_pullrequest(self):
        self.create_users([
            ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
        ])
        self.create_ldap(b'mjane@example.com', b'mjane', 2001, b'Mary Jane')

        self.reviewboard_login('mjane@example.com', 'password2')

        self.load_rburl('import-pullrequest/dminor/gecko-dev/1')

        btn = self.browser.find_element_by_id('mozreview-import-pullrequest-trigger');
        btn.click()

        element = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, "activity-indicator"))
        )

        # This should be present regardless of whether or not the request has
        # completed.
        self.assertTrue('Importing pull request' in element.text)

        # We need more work on the testing infrastructure for this to succeed,
        # but this does indicate that the request made it to Autoland.
        WebDriverWait(self.browser, 3).until(
            lambda x: "failed" in element.text)
