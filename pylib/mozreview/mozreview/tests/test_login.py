# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

from vcttesting.unittest import MozReviewWebDriverTest


class LoginTest(MozReviewWebDriverTest):
    def assertInvalidLogin(self):
        self.verify_rburl('account/login/')
        el = self.browser.find_elements_by_class_name('errorlist')
        self.assertEqual(len(el), 1)
        li = el[0].find_elements_by_tag_name('li')
        self.assertEqual(len(li), 1)
        self.assertIn('Please enter a correct username and password',
            li[0].text)


    def test_invalid_login(self):
        self.reviewboard_login('nobody', 'invalid', verify=False)
        self.assertInvalidLogin()

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
