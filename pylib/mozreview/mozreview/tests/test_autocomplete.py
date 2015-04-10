# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time

from selenium.webdriver.common.keys import Keys

from vcttesting.unittest import MozReviewWebDriverTest


class AutocompleteTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('joe@example.com', 'password', 'Joe Smith [:joe]'),
                ('jane@example.com', 'password', 'Jane Doe [:jane]'),
                ('bob@example.com', 'password', 'Bob Jones [:bob]'),
                ('peter@example.com', 'password', 'Peter Nonick'),
                ('joey@example.com', 'password', 'Joey Somebody [:joey]'),
            ])

            self.create_ldap(b'bob@example.com', b'bob', 2001, b'Bob User')

            bb = self.user_bugzilla('bob@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')
            lr = self.create_basic_repo('bob@example.com', 'bob')

            lr.write('foo', 'first')
            lr.run(['commit', '-m', 'Bug 1 - First commit'])
            lr.run(['push'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_autocomplete_results_appear(self):
        self.reviewboard_login('bob@example.com', 'password')
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()

        ac = self.prepare_edit_reviewers(0)
        ac.send_keys('joe')

        r = self.wait_for_autocomplete_results()
        lis = r.find_elements_by_tag_name('li')
        entries = [li.get_attribute('innerHTML') for li in lis]

        self.assertEqual(entries, [
            '<strong>joe</strong>',
            '<strong>joe</strong>y',
        ])

        ac.send_keys(Keys.ESCAPE)
        self.switch_to.alert.accept()

    def test_tab_complete(self):
        self.reviewboard_login('bob@example.com', 'password')
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()
        ac = self.prepare_edit_reviewers(0)
        ac.send_keys('joe')

        self.wait_for_autocomplete_results()
        ac.send_keys(Keys.ARROW_DOWN)
        ac.send_keys(Keys.TAB)

        self.assertEqual(ac.get_attribute('value'), 'joey, ',
                         'TAB completes autocomplete')

        ac.send_keys('jan')
        self.wait_for_autocomplete_results()
        ac.send_keys(Keys.TAB)
        self.assertEqual(ac.get_attribute('value'), 'joey, jane, ')

        commits = self.get_commits_el()
        cancel = commits.find_elements_by_class_name('cancel')[0]
        cancel.click()
        self.switch_to.alert.accept()

    def test_enter(self):
        self.reviewboard_login('bob@example.com', 'password')
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()
        ac = self.prepare_edit_reviewers(0)

        ac.send_keys('joey')
        self.wait_for_autocomplete_results()
        ac.send_keys(Keys.RETURN)

        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name('child-rr-reviewers')
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0].get_attribute('innerHTML'), 'joey, ')

        # TODO need a better method to wait for XHR saving the draft to finish.
        time.sleep(1)

        # Loading the page again will have the reviewer preserved.
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name('child-rr-reviewers')
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0].get_attribute('innerHTML'), 'joey')

        # Sending backspace should wipe out the reviewer.
        ac = self.prepare_edit_reviewers(0)
        ac.send_keys(Keys.BACKSPACE)
        ac.send_keys(Keys.RETURN)

        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name('child-rr-reviewers')
        self.assertEqual(len(reviewers), 1)
        self.assertEqual(reviewers[0].get_attribute('innerHTML'), '')

    def test_irc_syntax(self):
        """:nick syntax auto complete works."""
        self.reviewboard_login('bob@example.com', 'password')
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()
        ac = self.prepare_edit_reviewers(0)

        ac.send_keys(':joe')
        r = self.wait_for_autocomplete_results()

        lis = r.find_elements_by_tag_name('li')
        entries = [li.get_attribute('innerHTML') for li in lis]

        self.assertEqual(entries, [
            '<strong>joe</strong>',
            '<strong>joe</strong>y',
        ])

        ac.send_keys(Keys.ESCAPE)
        self.switch_to.alert.accept()
