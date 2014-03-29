# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

import contextlib
import os
import platform
import shutil
import sqlite3
import tempfile

from ConfigParser import RawConfigParser


def find_profiles(find_times=False):
    """Find Firefox profile directories.

    Returns an iterable of profile directories. The first entry is the
    active/default profile.
    """
    base = None

    if platform.system() == 'Darwin':
        from Carbon import Folder, Folders
        pathref = Folder.FSFindFolder(Folders.kUserDomain,
            Folders.kApplicationSupportFolderType,
            Folders.kDontCreateFolder)
        path = pathref.FSRefMakePath()
        base = os.path.join(path, 'Firefox')
    elif platform.system() == 'Windows':
        import ctypes
        SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        SHGetFolderPath.argtypes = [ctypes.c_void_p, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_int32, ctypes.c_wchar_p]
        path_buf = ctypes.create_unicode_buffer(1024)
        CSIDL_APPDATA = 26
        if not SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf):
            path = path_buf.value
            base = os.path.join(path_buf.value, 'Mozilla', 'Firefox')
    else:
        base = os.path.expanduser('~/.mozilla/firefox')

    if not base:
        return []

    ini_path = os.path.join(base, 'profiles.ini')
    c = RawConfigParser(allow_no_value=True)
    c.read([ini_path])

    paths = []

    for section in c.sections():
        if not c.has_option(section, 'Path'):
            continue

        profile_path = c.get(section, 'Path')
        is_relative = True
        if c.has_option(section, 'IsRelative'):
            is_relative = c.getboolean(section, 'IsRelative')

        if is_relative:
            profile_path = os.path.join(base, profile_path)

        is_default = False
        if c.has_option(section, 'Default'):
            is_default = c.getboolean(section, 'Default')

        name = c.get(section, 'Name')

        newest_time = None
        if find_times:
            for f in os.listdir(profile_path):
                full = os.path.join(profile_path, f)
                if not os.path.isfile(full):
                    continue

                mtime = os.path.getmtime(full)
                if not newest_time or mtime > newest_time:
                    newest_time = mtime

        paths.append((name, profile_path, is_default, newest_time))

    return paths


@contextlib.contextmanager
def sqlite_safe_open(path):
    """Helper to open SQLite databases in profiles.

    Firefox locks database files, preventing new connections. So, we need
    to copy the entire file and delete it when we're done.
    """
    tempdir = tempfile.mkdtemp()
    conn = None
    try:
        basename = os.path.basename(path)
        destpath = os.path.join(tempdir, '%s.copy.sqlite' % basename)

        shutil.copyfile(path, destpath)

        # Many databases use sqlite's WAL feature, which bumps the sqlite
        # version number. Older clients may refuse to open the db if the
        # version is too new. Patch the version number to an older version
        # so we can open it. The version only impacts the journalling, so
        # this should be relatively safe.
        with open(destpath, 'r+b') as fh:
            fh.seek(18, 0)
            fh.write('\x01\x01')

        conn = sqlite3.connect(destpath)
        yield conn
    finally:
        if conn:
            conn.close()
        shutil.rmtree(tempdir)


def get_cookies(profile_path, host=None):
    """Obtain cookies from the profile.

    Returns an iterable of dicts containing the raw entries from the cookies
    database.

    host can be specified as a unicode string or an iterable of hostnames to
    limit results to.
    """
    with sqlite_safe_open(os.path.join(profile_path, 'cookies.sqlite')) as db:
        if host:
            host = host.lstrip('.')
            result = db.execute('SELECT * FROM moz_cookies WHERE host=? or host=?',
                (host, '.%s' % host))
        else:
            result = db.execute('SELECT * FROM moz_cookies')

        for row in result:
            yield {col[0]: row[i] for i, col in enumerate(result.description)}
