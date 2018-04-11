# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import io
import os
import sys
import unittest

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'autoland')))

from patch_helper import PatchHelper


class TestTransplant(unittest.TestCase):
    def test_is_diff_line(self):
        self.assertTrue(PatchHelper._is_diff_line('diff --git a/file b/file'))
        self.assertTrue(PatchHelper._is_diff_line('diff a/file b/file'))
        self.assertTrue(PatchHelper._is_diff_line('diff -r 23280edf8655 autoland/autoland/patch_helper.py'))
        self.assertFalse(PatchHelper._is_diff_line('cheese'))
        self.assertFalse(PatchHelper._is_diff_line('diff'))
        self.assertFalse(PatchHelper._is_diff_line('diff '))
        self.assertFalse(PatchHelper._is_diff_line('diff file'))

    def test_vanilla(self):
        patch = PatchHelper(io.BytesIO("""
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
WIP transplant and diff-start-line

diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()))

        self.assertEqual(patch.header('Date'),
                         '1523427125 -28800')
        self.assertEqual(patch.header('Node ID'),
                         '3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07')
        self.assertEqual(patch.header('User'),
                         'byron jones <glob@mozilla.com>')
        self.assertEqual(patch.header('Parent'),
                         '46c36c18528fe2cc780d5206ed80ae8e37d3545d')

        self.assertEqual(patch.commit_description(),
                         'WIP transplant and diff-start-line')

    def test_start_line(self):
        patch = PatchHelper(io.BytesIO("""
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
# Diff Start Line 10
WIP transplant and diff-start-line

diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()))

        self.assertEqual(patch.header('Diff Start Line'),
                         '10')

        self.assertEqual(patch.commit_description(),
                         'WIP transplant and diff-start-line')

    def test_no_header(self):
        patch = PatchHelper(io.BytesIO("""
WIP transplant and diff-start-line

diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()))

        self.assertIsNone(patch.header('User'))

        self.assertEqual(patch.commit_description(),
                         'WIP transplant and diff-start-line')

    def test_diff_inject_no_start_line(self):
        patch = PatchHelper(io.BytesIO("""
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
WIP transplant and diff-start-line

diff --git a/bad b/bad
@@ -0,0 +0,0 @@
blah

diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()))

        self.assertEqual(patch.commit_description(),
                         'WIP transplant and diff-start-line')

    def test_diff_inject_start_line(self):
        patch = PatchHelper(io.BytesIO("""
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
# Diff Start Line 14
WIP transplant and diff-start-line

diff --git a/bad b/bad
@@ -0,0 +0,0 @@
blah

diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()))

        self.assertEqual(patch.commit_description(),
                         'WIP transplant and diff-start-line\n'
                         '\n'
                         'diff --git a/bad b/bad\n'
                         '@@ -0,0 +0,0 @@\n'
                         'blah')

    def test_write_start_line(self):
        header = """
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
# Diff Start Line 10
""".strip()
        commit_desc = """
WIP transplant and diff-start-line
""".strip()
        diff = """
diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()
        patch = PatchHelper(
            io.BytesIO('%s\n%s\n\n%s' % (header, commit_desc, diff)))

        buf = io.BytesIO('')
        patch.write_commit_description(buf)
        self.assertEqual(buf.getvalue(), commit_desc)

        buf = io.BytesIO('')
        patch.write_diff(buf)
        self.assertEqual(buf.getvalue(), diff)

    def test_write_no_start_line(self):
        header = """
# HG changeset patch
# User byron jones <glob@mozilla.com>
# Date 1523427125 -28800
#      Wed Apr 11 14:12:05 2018 +0800
# Node ID 3379ea3cea34ecebdcb2cf7fb9f7845861ea8f07
# Parent  46c36c18528fe2cc780d5206ed80ae8e37d3545d
""".strip()
        commit_desc = """
WIP transplant and diff-start-line
""".strip()
        diff = """
diff --git a/autoland/autoland/transplant.py b/autoland/autoland/transplant.py
--- a/autoland/autoland/transplant.py
+++ b/autoland/autoland/transplant.py
@@ -318,24 +318,58 @@ class PatchTransplant(Transplant):
# instead of passing the url to 'hg import' to make
...
""".strip()
        patch = PatchHelper(
            io.BytesIO('%s\n%s\n\n%s' % (header, commit_desc, diff)))

        buf = io.BytesIO('')
        patch.write_commit_description(buf)
        self.assertEqual(buf.getvalue(), commit_desc)

        buf = io.BytesIO('')
        patch.write_diff(buf)
        self.assertEqual(buf.getvalue(), diff)
