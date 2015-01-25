# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os
import shutil
import tempfile
import unittest

from selenium import webdriver

from vcttesting.mozreview import MozReview


class MozReviewTest(unittest.TestCase):
    """A base class used for testing MozReview instances.

    When instances of this test class are instantiated, we set up a MozReview
    instance.

    The MozReview instance is available for the lifetime of the test class.
    i.e. it is shared between all test functions.
    """

    @classmethod
    def setUpClass(cls):
        tmpdir = tempfile.mkdtemp()
        cls._tmpdir = tmpdir

        mr = MozReview(tmpdir)

        cls.mr = mr
        mr.start(db_image=os.environ['DOCKER_BMO_DB_IMAGE'],
                 web_image=os.environ['DOCKER_BMO_WEB_IMAGE'],
                 pulse_image=os.environ['DOCKER_PULSE_IMAGE'])

    @classmethod
    def tearDownClass(cls):
        cls.mr.stop()
        shutil.rmtree(cls._tmpdir)

    @property
    def bzurl(self):
        return self.mr.bugzilla_url

    @property
    def rburl(self):
        return self.mr.reviewboard_url

    @property
    def hgurl(self):
        return self.mr.mercurial_url


class MozReviewWebDriverTest(MozReviewTest):
    """A base class used for testing MozReview instances.

    When instances of this test class are instantiated, we set up a MozReview
    instance and prepare the Selenium WebDriver connection to that instance.

    This test thus facilitates the easy testing of web browser interaction with
    MozReview server components.
    """

    @classmethod
    def setUpClass(cls):
        MozReviewTest.setUpClass()
        cls.browser = webdriver.Firefox()

    def setUp(self):
        self.addCleanup(self.browser.quit)
