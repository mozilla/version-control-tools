# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import unittest

from vcttesting.unittest import MozReviewWebDriverTest


@unittest.skip('Skipped due to Bug 1348725')
class ReviewerStatusTest(MozReviewWebDriverTest):

    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])
            self.create_ldap(b'mjane@example.com',
                             b'mjane', 2001, b'Mary Jane')
            mjb = self.user_bugzilla('mjane@example.com')
            mjb.create_bug('TestProduct', 'TestComponent', 'bug1')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change\n')
            lr.run(['commit', '-m', 'Bug 1 - Test autocomplete; r?jsmith'])
            lr.write('foo', 'second change\n')
            lr.run(['commit', '-m', 'This is the second commit; r?jsmith'])
            lr.write('foo', 'third change\n')
            lr.run(['commit', '-m', 'This is the third commit; r?jsmith'])
            lr.run(['push'])
        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def test_pending_review(self):
        """A reviewer initial status is pending"""
        self.load_rburl('r/1')
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        reviewer = reviewers[0].find_elements_by_class_name('reviewer-name')
        self.assertEqual(reviewer[0].get_attribute('innerHTML'), 'jsmith')
        self.assertEqual(reviewer[0].get_attribute('class'), 'reviewer-name')

    def test_review_given_without_shipit(self):
        """A review without ship-it still doesn't change the reviewer status"""
        self.reviewboard_login('jsmith@example.com', 'password1')
        self.add_review(2, text='First review')
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        reviewer = reviewers[0].find_elements_by_class_name('reviewer-name')
        self.assertEqual(reviewer[0].get_attribute('innerHTML'), 'jsmith')
        self.assertEqual(reviewer[0].get_attribute('class'), 'reviewer-name')

    def test_review_given_with_shipit(self):
        """A review with ship-it change the reviewer status"""
        self.reviewboard_login('jsmith@example.com', 'password1')
        self.add_review(3, text='Second review', ship_it=True)
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        reviewer = reviewers[1].find_elements_by_class_name('reviewer-name')
        self.assertEqual(reviewer[0].get_attribute('innerHTML'), 'jsmith')
        self.assertEqual(reviewer[0].get_attribute('class'),
                         'reviewer-name reviewer-ship-it')

    def test_last_review_status_only(self):
        """Only the last review determines the reviewer status"""
        self.reviewboard_login('jsmith@example.com', 'password1')

        self.add_review(4, text='Third review', ship_it=True)
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        reviewer = reviewers[2].find_elements_by_class_name('reviewer-name')
        self.assertEqual(reviewer[0].get_attribute('innerHTML'), 'jsmith')
        self.assertEqual(reviewer[0].get_attribute('class'),
                         'reviewer-name reviewer-ship-it')

        self.add_review(4, text='Fourth review', ship_it=False)
        self.wait_for_reviewers_to_load()
        commits = self.get_commits_el()
        reviewers = commits.find_elements_by_class_name(
            'mozreview-child-reviewer-list')
        reviewer = reviewers[2].find_elements_by_class_name('reviewer-name')
        self.assertEqual(reviewer[0].get_attribute('innerHTML'), 'jsmith')
        self.assertEqual(reviewer[0].get_attribute('class'), 'reviewer-name')
