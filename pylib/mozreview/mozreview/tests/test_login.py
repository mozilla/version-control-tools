# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest

from vcttesting.unittest import MozReviewWebDriverTest


@unittest.skip('Skipped due to Bug 1348725')
class LoginTest(MozReviewWebDriverTest):
    def assertInvalidLogin(self, verify_error_msg=True):
        self.verify_bzurl('auth.cgi')
        if verify_error_msg:
            el = self.browser.find_element_by_id('error_msg')
            self.assertIn('The username or password you entered is not valid',
                          el.text)

    def test_invalid_login(self):
        self.reviewboard_login('nobody', 'invalid', verify=False)
        # The Bugzilla login form uses type="email" in the login field.
        # Since this means we can't submit the form with the username
        # 'nobody' (not a valid email address), we won't get the standard
        # invalid-login error message.
        self.assertInvalidLogin(verify_error_msg=False)

    def test_username_login_disallowed(self):
        self.bugzilla().create_user('baduser@example.com', 'password1',
                                    'Some User [:user1]')

        self.reviewboard_login('user1', 'password1', verify=False)
        self.assertInvalidLogin()

    def test_invalid_password(self):
        self.bugzilla().create_user('badpass@example.com', 'password2',
                                    'Bad Password')
        self.reviewboard_login('badpass@example.com', 'badpassword',
                               verify=False)
        self.assertInvalidLogin()

    def test_good_login(self):
        self.bugzilla().create_user('gooduser@example.com', 'password3',
                                    'Good User')
        self.reviewboard_login('gooduser@example.com', 'password3')
