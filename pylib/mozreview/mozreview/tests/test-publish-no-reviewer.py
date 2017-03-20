# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time
import unittest

from selenium.webdriver.common.by import (
    By,
)
from selenium.webdriver.common.keys import (
    Keys,
)
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.wait import (
    WebDriverWait,
)

from vcttesting.unittest import (
    MozReviewWebDriverTest,
)


@unittest.skip('Skipped due to Bug 1348725')
class PublishNoReviewerTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmoth@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com', b'mjane', 2001,
                             b'Mary Jane', scm_level=3)

            mjb = self.user_bugzilla('mjane@example.com')
            mjb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test publish; r?jsmith'])
            lr.run(['push', '--config', 'reviewboard.autopublish=false'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_publish_no_reviewers(self):
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()

        ac = self.prepare_edit_reviewers(0)
        ac.send_keys(Keys.BACKSPACE)
        ac.send_keys(Keys.RETURN)

        # TODO need a better method to wait for XHR saving the draft.
        time.sleep(1)

        publish_button = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID, 'btn-draft-publish')))
        publish_button.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))
