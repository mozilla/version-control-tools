# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os
import shutil
import sqlite3
import tempfile
import time
import unittest

# TRACKING py3
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

import mozhg.auth as auth


def create_cookies_db(profiledir):
    """Create a cookies SQLite database as used by Firefox profiles."""
    path = os.path.join(profiledir, b"cookies.sqlite")

    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE moz_cookies "
            "(id INTEGER PRIMARY KEY, "
            "baseDomain TEXT, "
            "appId INTEGER DEFAULT 0, "
            "inBrowserElement INTEGER DEFAULT 0, "
            "name TEXT, "
            "value TEXT, "
            "host TEXT, "
            "path TEXT, "
            "expiry INTEGER, "
            "lastAccessed INTEGER, "
            "creationTime INTEGER, "
            "isSecure INTEGER, "
            "isHttpOnly INTEGER, "
            "CONSTRAINT moz_uniqueid UNIQUE (name, host, path, appId, inBrowserElement))"
        )


def create_login_cookie(profiledir, url, userid, cookie):
    """Create a Bugzilla login cookie."""
    path = os.path.join(profiledir, b"cookies.sqlite")
    if not os.path.exists(path):
        create_cookies_db(profiledir)

    with sqlite3.connect(path) as db:
        # The time values shouldn't matter.
        expiry = int(time.time()) + 3600
        last_accessed = int(time.time()) * 1000
        creation_time = int(time.time()) * 1000

        url = urlparse.urlparse(url.decode("utf-8"))
        domain = ".".join(url.hostname.split(".")[-2:])
        host = url.hostname
        path = url.path

        sql = " ".join(
            [
                "INSERT INTO moz_cookies (baseDomain, name, value, host, path,",
                "expiry, lastAccessed, creationTime, isSecure, isHttpOnly)",
                "VALUES (:base_domain, :name, :value, :host, :path, :expiry,",
                ":last_accessed, :creation_time, :is_secure, :is_http_only)",
            ]
        )
        params = dict(
            base_domain=domain,
            name="Bugzilla_login",
            value=userid,
            host=host,
            path=path,
            expiry=expiry,
            last_accessed=last_accessed,
            creation_time=creation_time,
            is_secure=1,
            is_http_only=1,
        )

        db.execute(sql, params)
        params["name"] = "Bugzilla_logincookie"
        params["value"] = cookie
        db.execute(sql, params)


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp().encode("utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def p(self, *parts):
        return os.path.join(self.tmpdir, *parts)

    def test_container(self):
        a = auth.BugzillaAuth(username="user", password="pass")

        self.assertEqual(a.username, "user")
        self.assertEqual(a.password, "pass")
        self.assertIsNone(a.cookie)
        self.assertEqual(a._type, b"explicit")

    def test_get_profiles_empty(self):
        """If we point at a directory without a profiles.ini, we get nothing."""
        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(profiles, [])

    def test_get_profiles_single(self):
        """A profiles.ini with a single profile works as expected."""
        with open(self.p(b"profiles.ini"), "wb") as fh:
            fh.write(
                b"\n".join(
                    [
                        b"[General]",
                        b"StartWithLastProfile=0",
                        b"",
                        b"[Profile0]",
                        b"Name=default",
                        b"IsRelative=1",
                        b"Path=Profiles.jmt0dxx7.default",
                    ]
                )
            )

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(len(profiles), 1)
        self.assertEqual(
            profiles[0],
            {
                b"name": b"default",
                b"path": self.p(b"Profiles.jmt0dxx7.default"),
                b"default": False,
                b"mtime": -1,
            },
        )

        with open(self.p(b"profiles.ini"), "ab") as fh:
            fh.write(b"\nDefault=1\n")

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(len(profiles), 1)
        self.assertTrue(profiles[0][b"default"])

    def test_multiple_profiles_default_first(self):
        """Test that the default profile always comes first."""
        with open(self.p(b"profiles.ini"), "wb") as fh:
            fh.write(
                b"\n".join(
                    [
                        b"[Profile0]",
                        b"Name=notdefault",
                        b"IsRelative=1",
                        b"Path=notdefault",
                        b"",
                        b"[Profile1]",
                        b"Name=default",
                        b"IsRelative=1",
                        b"Path=default",
                        b"Default=1",
                    ]
                )
            )

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(
            profiles,
            [
                {
                    b"name": b"default",
                    b"path": self.p(b"default"),
                    b"default": True,
                    b"mtime": -1,
                },
                {
                    b"name": b"notdefault",
                    b"path": self.p(b"notdefault"),
                    b"default": False,
                    b"mtime": -1,
                },
            ],
        )

    def test_multiple_profiles_age_ordering(self):
        """Profile with newest file content comes first."""
        with open(self.p(b"profiles.ini"), "wb") as fh:
            fh.write(
                b"\n".join(
                    [
                        b"[Profile0]",
                        b"Name=foo",
                        b"IsRelative=1",
                        b"Path=foo",
                        b"",
                        b"[Profile1]",
                        b"Name=bar",
                        b"IsRelative=1",
                        b"Path=bar",
                        b"",
                        b"[Profile2]",
                        b"Name=baz",
                        b"IsRelative=1",
                        b"Path=baz",
                        b"Default=1",
                    ]
                )
            )

        for p in [b"foo", b"bar", b"baz"]:
            os.mkdir(self.p(p))
            os.mkdir(self.p(p, b"dummydir"))
            with open(self.p(p, b"dummy1"), "a"):
                pass

        now = int(time.time())
        t_foo = now - 10
        t_bar = now - 5
        t_baz = now - 7

        os.utime(self.p(b"foo", b"dummy1"), (t_foo, t_foo))
        os.utime(self.p(b"bar", b"dummy1"), (t_bar, t_bar))
        os.utime(self.p(b"baz", b"dummy1"), (t_baz, t_baz))

        profiles = auth.get_profiles(self.tmpdir)
        names = [p[b"name"] for p in profiles]
        self.assertEqual(names, [b"baz", b"bar", b"foo"])

    def test_find_profiles_path(self):
        # This should always work on all supported systems.
        path = auth.find_profiles_path()
        self.assertIsNotNone(path)

        try:
            os.environ["FIREFOX_PROFILES_DIR"] = self.tmpdir.decode("utf-8")
            self.assertEqual(auth.find_profiles_path(), self.tmpdir)
        finally:
            del os.environ["FIREFOX_PROFILES_DIR"]

    def test_cookie_no_db(self):
        """Ensure we react sanely when no cookies.sqlite file is present."""
        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(
            self.tmpdir, "http://dummy"
        )
        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def test_cookie_empty_db(self):
        """Ensure empty cookies.db behaves properly."""
        create_cookies_db(self.tmpdir)

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(
            self.tmpdir, "http://dummy"
        )
        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def test_get_cookie_simple(self):
        create_login_cookie(
            self.tmpdir, b"https://bugzilla.mozilla.org/", "userid", "cookievalue"
        )

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(
            self.tmpdir, "https://bugzilla.mozilla.org"
        )
        self.assertEqual(userid, b"userid")
        self.assertEqual(cookie, b"cookievalue")

    def test_get_cookie_no_host(self):
        """If we request a cookie from another host, we shouldn't get a cookie."""
        create_login_cookie(self.tmpdir, b"https://example.com/", "userid", "cookie")
        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(
            self.tmpdir, "https://bugzilla.mozilla.org"
        )

        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def test_get_cookie_multiple_paths(self):
        """If we have multiple cookies for a domain, one with correct path is used."""
        create_login_cookie(
            self.tmpdir,
            b"https://bugzilla.mozilla.org/production/",
            "produser",
            "prodpass",
        )
        create_login_cookie(
            self.tmpdir,
            b"https://bugzilla.mozilla.org/testing/",
            "testuser",
            "testpass",
        )

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(
            self.tmpdir, "https://bugzilla.mozilla.org/testing/"
        )
        self.assertEqual(userid, b"testuser")
        self.assertEqual(cookie, b"testpass")
