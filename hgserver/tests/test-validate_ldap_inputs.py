#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Unit tests for `validate_ldap_inputs`.

import unittest

from hgmolib.ldap_helper import (
    assert_ldap_args_valid,
    validate_ldap_inputs,
)


class TestRepoNameValidation(unittest.TestCase):
    def test_validate_ldap_inputs(self):
        @validate_ldap_inputs
        def testfunc(arg1, arg2, kwarg1="", kwarg2=""):
            # Return `True` here as we `assertTrue` later.
            return True

        # Invalid arguments should cause a raise.
        with self.assertRaises(ValueError):
            testfunc("\\x00a", "a", kwarg1="a", kwarg2="a")

        with self.assertRaises(ValueError):
            testfunc("a", "\\x00a", kwarg1="a", kwarg2="a")

        with self.assertRaises(ValueError):
            testfunc("a", "a", kwarg1="\\x00a", kwarg2="a")

        with self.assertRaises(ValueError):
            testfunc("a", "a", kwarg1="a", kwarg2="\\x00a")

        # Valid arguments should not raise.
        self.assertTrue(testfunc("a", "a", kwarg1="a", kwarg2="a"))

    def test_assert_ldap_args_valid(self):
        # Valid arguments.
        for arg in ("hello", "cosheehan@mozilla.com", "hgAccountEnabled"):
            self.assertTrue(assert_ldap_args_valid(arg) is None)

        # Invalid arguments.
        for arg in (
            "blah\x00",
            "blah\\",
            "cosheehan@mozilla.com\\blah",
        ):
            with self.assertRaises(ValueError):
                assert_ldap_args_valid(arg)


if __name__ == "__main__":
    unittest.main()
