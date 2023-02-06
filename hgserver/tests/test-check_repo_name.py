#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Unit tests for assert_valid_repo_name

import os
import sys
import unittest

here = os.path.abspath(os.path.dirname(__file__))
sys.path.append("%s/../pash" % here)
from hg_helper import is_valid_repo_name


class TestRepoNameValidation(unittest.TestCase):
    def test_valid(self):
        for name in [
            "reponame",
            "repo/name",
            "100repos",
            "1.repo.name",
            "1-repo-name",
            "1_repo_name",
            "reponame/",
        ]:
            self.assertTrue(is_valid_repo_name(name))

    def test_invalid(self):
        for name in [
            "/reop",
            ".repo",
            "repo/.name",
            "repo/../name",
            "~name/repo",
            "!repo",
            "re!po",
            "re po",
            "re\tpo",
            "re\x82po",
            "re\x00po",
            "--switch",
            "repo/--switch",
            ".hg",
            ".git",
            ".hg/repo",
            ".git/repo",
            "repo.hg",
            "prefix/repo.hg",
            "repo.git",
            "prefix/repo.git",
        ]:
            self.assertFalse(is_valid_repo_name(name))


if __name__ == "__main__":
    unittest.main()
