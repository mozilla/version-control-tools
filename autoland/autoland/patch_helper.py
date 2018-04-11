# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

HEADER_NAMES = ('User', 'Date', 'Node ID', 'Parent', 'Diff Start Line')
DIFF_LINE_RE = re.compile(r'^diff\s+\S+\s+\S+')


class PatchHelper(object):
    """Helper class for parsing Mercurial patches/exports."""

    def __init__(self, fileobj):
        self.patch = fileobj
        self.headers = {}
        self.header_end_line_no = 0
        self._parse_header()

        # "Diff Start Line" is a lando/transplant extension.
        self.diff_start_line = self.header('Diff Start Line')
        if self.diff_start_line:
            try:
                self.diff_start_line = int(self.diff_start_line)
            except ValueError:
                self.diff_start_line = None

    @staticmethod
    def _is_diff_line(line):
        return DIFF_LINE_RE.search(line)

    @staticmethod
    def _header_value(line, prefix):
        m = re.search(r'^#\s+' + re.escape(prefix) + '\s+(.*)', line,
                      flags=re.IGNORECASE)
        if not m:
            return None
        return m.group(1).strip()

    def _parse_header(self):
        """Extract header values specified by HEADER_NAMES."""
        try:
            for line in self.patch:
                if not line.startswith('# '):
                    break
                self.header_end_line_no += 1
                for name in HEADER_NAMES:
                    value = self._header_value(line, name)
                    if value:
                        self.headers[name.lower()] = value
                        break
        finally:
            self.patch.seek(0)

    def header(self, name):
        """Returns value of the specified header, or None if missing."""
        return self.headers.get(name.lower())

    def commit_description(self):
        """Returns the commit description."""
        try:
            line_no = 0
            commit_desc = []
            for line in self.patch:
                line_no += 1

                if line_no <= self.header_end_line_no:
                    continue

                if self.diff_start_line:
                    if line_no == self.diff_start_line:
                        break
                    commit_desc.append(line)
                else:
                    if self._is_diff_line(line):
                        break
                    commit_desc.append(line)

            return ''.join(commit_desc).strip()
        finally:
            self.patch.seek(0)

    def write(self, f):
        """Writes whole patch to the specified file object."""
        try:
            while 1:
                buf = self.patch.read(16*1024)
                if not buf:
                    break
                f.write(buf)
        finally:
            self.patch.seek(0)

    def write_commit_description(self, f):
        """Writes the commit description to the specified file object."""
        f.write(self.commit_description())

    def write_diff(self, f):
        """Writes the diff to the specified file object."""
        try:
            line_no = 0
            for line in self.patch:
                line_no += 1

                if self.diff_start_line:
                    if line_no == self.diff_start_line:
                        f.write(line)
                        break
                else:
                    if self._is_diff_line(line):
                        f.write(line)
                        break

            while 1:
                buf = self.patch.read(16*1024)
                if not buf:
                    break
                f.write(buf)
        finally:
            self.patch.seek(0)
