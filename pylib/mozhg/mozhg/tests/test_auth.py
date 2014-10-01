# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import unittest

import mozhg.auth as auth

class TestAuth(unittest.TestCase):
    def test_container(self):
        a = auth.BugzillaAuth(username='user', password='pass')

        self.assertEqual(a.username, 'user')
        self.assertEqual(a.password, 'pass')
        self.assertIsNone(a.cookie)
        self.assertEqual(a._type, 'explicit')
