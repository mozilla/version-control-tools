# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import time
import unittest

import requests
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import (ElementNotVisibleException,
                                        NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from vcttesting.unittest import MozReviewWebDriverTest


def get_treestatus_login_token(treestatus_url, user, password):

    r = requests.get(treestatus_url + '/login', allow_redirects=False,
                     auth=(user, password))
    r.raise_for_status()
    return r.headers['x-treestatus-token']


def add_tree(treestatus_url, tree,
             user='sheriff@example.com', password='password'):
    login_token = get_treestatus_login_token(treestatus_url, user, password)
    data = {
        'newtree': tree,
        'token': login_token,
    }
    r = requests.post(treestatus_url + '/mtree', data=data,
                      auth=(user, password))
    r.raise_for_status()


def close_tree(treestatus_url, tree,
               user='sheriff@example.com', password='password'):
    login_token = get_treestatus_login_token(treestatus_url, user, password)
    data = {
        'status': 'closed',
        'tags': 'Other',
        'token': login_token,
        'tree': tree,
        'reason': '',
        'remember': '',
    }
    r = requests.post(treestatus_url + '/', data=data,
                      auth=(user, password))
    r.raise_for_status()


@unittest.skip('Skipped due to Bug 1246950')
class AutolandConcurrentTest(MozReviewWebDriverTest):
    @classmethod
    def setUpClass(cls):
        MozReviewWebDriverTest.setUpClass()

        try:
            self = cls('run')
            self.create_users([
                ('jsmith@example.com', 'password1', 'Jeremy Smith [:jsmith]'),
                ('mjane@example.com', 'password2', 'Mary Jane [:mary]'),
            ])

            self.create_ldap(b'mjane@example.com', b'mjane', 2001,
                             b'Mary Jane')

            bb = self.user_bugzilla('mjane@example.com')
            bb.create_bug('TestProduct', 'TestComponent', 'First Bug')

            lr = self.create_basic_repo('mjane@example.com', 'mjane')
            lr.write('foo', 'first change')
            lr.run(['commit', '-m', 'Bug 1 - Test try'])
            lr.run(['push'])

            # create try tree
            add_tree(self.mr.treestatus_url, 'try')
            close_tree(self.mr.treestatus_url, 'try')

        except Exception:
            MozReviewWebDriverTest.tearDownClass()
            raise

    def send_autoland_try_request(self, try_syntax='try: stuff'):
        automation_menu = self.browser.find_element_by_id('automation-menu')
        automation_menu.click()
        try_btn = self.browser.find_element_by_id('autoland-try-trigger')
        self.assertEqual(
            try_btn.value_of_css_property('opacity'), '1')

        # Clicking the button should display a trychooser dialog
        try_btn.click()
        try_text = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located(
                (By.ID, 'mozreview-autoland-try-syntax'))
            )
        try_text.send_keys(try_syntax)
        try_submit = self.browser.find_element_by_xpath(
            '//input[@value="Submit"]')

        # clicking the Submit button should display an activity indicator
        try_submit.click()

    def test_autoland_try_concurrent(self):
        # We currently have four conditions for enabling the 'automation' menu
        # and try button (see static/mozreview/js/autoland.js):
        # 1. The review must be published
        # 2. The review must be mutable by the current user
        # 3. The user must have scm_level_1 or higher
        # 4. The repository must have an associated try repository
        # TODO: Ideally we'd test these conditions independently to ensure that
        #       the 'try' button will only show up when all four are met
        #       and not otherwise.

        # We should not be able to trigger a Try run without a HostingService
        # with an associated try repository.
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')
        try_btn = self.browser.find_element_by_id('autoland-try-trigger')
        self.assertEqual(
            try_btn.value_of_css_property('opacity'), '0.5')
        self.add_hostingservice(1, 'Sirius Black', 'scm_level_1',
                                'ssh://hg.example.com/try',
                                'ssh://hg.example.com/mainline', '')

        # We should also not be able to trigger a Try run unless the review is
        # published.
        self.reviewboard_login('mjane@example.com', 'password2')
        self.load_rburl('r/1')
        try_btn = self.browser.find_element_by_id('autoland-try-trigger')
        self.assertEqual(
            try_btn.value_of_css_property('opacity'), '0.5')
        self.assign_reviewer(0, 'jsmith')
        publish_btn = WebDriverWait(self.browser, 3).until(
            EC.visibility_of_element_located((By.ID,
                                              'btn-draft-publish')))
        publish_btn.click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.ID, 'draft-banner')))

        # Attempt to make intermittent failure with opacity of 'try' button
        # less common. See Bug 1220733.
        self.load_rburl('r/2')
        self.load_rburl('r/1')

        self.send_autoland_try_request()

        element = WebDriverWait(self.browser, 5).until(
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

        self.browser.refresh()

        # We should not be able to trigger a second Try run because the trees
        # are closed so the previous request is still pending.
        self.send_autoland_try_request()
        error_msg = WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '#activity-indicator .error_msg')
            )
        )

        self.assertEqual(error_msg.text,
                         ('An autoland request for this review '
                          'request is already in progress. '
                          'Please wait for that request to finish.'))
