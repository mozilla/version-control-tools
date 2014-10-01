# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os
import shutil
import sqlite3
import tempfile
import time
import unittest
import urlparse

import mozhg.auth as auth

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def p(self, *parts):
        return os.path.join(self.tmpdir, *parts)

    def test_container(self):
        a = auth.BugzillaAuth(username='user', password='pass')

        self.assertEqual(a.username, 'user')
        self.assertEqual(a.password, 'pass')
        self.assertIsNone(a.cookie)
        self.assertEqual(a._type, 'explicit')

    def test_get_profiles_empty(self):
        """If we point at a directory without a profiles.ini, we get nothing."""
        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(profiles, [])

    def test_get_profiles_single(self):
        """A profiles.ini with a single profile works as expected."""
        with open(self.p('profiles.ini'), 'wb') as fh:
            fh.write('\n'.join([
                '[General]',
                'StartWithLastProfile=0',
                '',
                '[Profile0]',
                'Name=default',
                'IsRelative=1',
                'Path=Profiles.jmt0dxx7.default',
            ]))

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0], {
            'name': 'default',
            'path': self.p('Profiles.jmt0dxx7.default'),
            'default': False,
            'mtime': -1,
        })

        with open(self.p('profiles.ini'), 'ab') as fh:
            fh.write('\nDefault=1\n')

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(len(profiles), 1)
        self.assertTrue(profiles[0]['default'])

    def test_multiple_profiles_default_first(self):
        """Test that the default profile always comes first."""
        with open(self.p('profiles.ini'), 'wb') as fh:
            fh.write('\n'.join([
                '[Profile0]',
                'Name=notdefault',
                'IsRelative=1',
                'Path=notdefault',
                '',
                '[Profile1]',
                'Name=default',
                'IsRelative=1',
                'Path=default',
                'Default=1',
            ]))

        profiles = auth.get_profiles(self.tmpdir)
        self.assertEqual(profiles, [
            {
                'name': 'default',
                'path': self.p('default'),
                'default': True,
                'mtime': -1,
            },
            {
                'name': 'notdefault',
                'path': self.p('notdefault'),
                'default': False,
                'mtime': -1,
            }
        ])

    def test_multiple_profiles_age_ordering(self):
        """Profile with newest file content comes first."""
        with open(self.p('profiles.ini'), 'wb') as fh:
            fh.write('\n'.join([
                '[Profile0]',
                'Name=foo',
                'IsRelative=1',
                'Path=foo',
                '',
                '[Profile1]',
                'Name=bar',
                'IsRelative=1',
                'Path=bar',
                '',
                '[Profile2]',
                'Name=baz',
                'IsRelative=1',
                'Path=baz',
                'Default=1',
            ]))

        for p in ['foo', 'bar', 'baz']:
            os.mkdir(self.p(p))
            os.mkdir(self.p(p, 'dummydir'))
            with open(self.p(p, 'dummy1'), 'a'):
                pass

        now = int(time.time())
        t_foo = now - 10
        t_bar = now - 5
        t_baz = now - 7

        os.utime(self.p('foo', 'dummy1'), (t_foo, t_foo))
        os.utime(self.p('bar', 'dummy1'), (t_bar, t_bar))
        os.utime(self.p('baz', 'dummy1'), (t_baz, t_baz))

        profiles = auth.get_profiles(self.tmpdir)
        names = [p['name'] for p in profiles]
        self.assertEqual(names, ['baz', 'bar', 'foo'])

    def test_cookie_no_db(self):
        """Ensure we react sanely when no cookies.sqlite file is present."""
        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(self.tmpdir, 'http://dummy')
        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def _create_cookies_db(self, profiledir):
        path = os.path.join(profiledir, 'cookies.sqlite')

        with sqlite3.connect(path) as db:
            db.execute(
                'CREATE TABLE moz_cookies '
                '(id INTEGER PRIMARY KEY, '
                'baseDomain TEXT, '
                'appId INTEGER DEFAULT 0, '
                'inBrowserElement INTEGER DEFAULT 0, '
                'name TEXT, '
                'value TEXT, '
                'host TEXT, '
                'path TEXT, '
                'expiry INTEGER, '
                'lastAccessed INTEGER, '
                'creationTime INTEGER, '
                'isSecure INTEGER, '
                'isHttpOnly INTEGER, '
                'CONSTRAINT moz_uniqueid UNIQUE (name, host, path, appId, inBrowserElement))')

    def _create_login_cookie(self, profiledir, url, userid, cookie):
        path = os.path.join(profiledir, 'cookies.sqlite')
        if not os.path.exists(path):
            self._create_cookies_db(profiledir)

        with sqlite3.connect(path) as db:
            # The time values shouldn't matter.
            expiry = int(time.time()) + 3600
            last_accessed = int(time.time()) * 1000
            creation_time = int(time.time()) * 1000

            url = urlparse.urlparse(url)
            domain = '.'.join(url.hostname.split('.')[-2:])
            host = url.hostname
            path = url.path

            sql = ' '.join([
                'INSERT INTO moz_cookies (baseDomain, name, value, host, path,',
                'expiry, lastAccessed, creationTime, isSecure, isHttpOnly)',
                'VALUES (:base_domain, :name, :value, :host, :path, :expiry,',
                ':last_accessed, :creation_time, :is_secure, :is_http_only)',
            ])
            params = dict(
                base_domain=domain,
                name='Bugzilla_login',
                value=userid,
                host=host,
                path=path,
                expiry=expiry,
                last_accessed=last_accessed,
                creation_time=creation_time,
                is_secure=1,
                is_http_only=1)

            db.execute(sql, params)
            params['name'] = 'Bugzilla_logincookie'
            params['value'] = cookie
            db.execute(sql, params)

    def test_cookie_empty_db(self):
        """Ensure empty cookies.db behaves properly."""
        self._create_cookies_db(self.tmpdir)

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(self.tmpdir,
                'http://dummy')
        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def test_get_cookie_simple(self):
        self._create_login_cookie(self.tmpdir, 'https://bugzilla.mozilla.org/',
                'userid', 'cookievalue')

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(self.tmpdir,
                'https://bugzilla.mozilla.org')
        self.assertEqual(userid, 'userid')
        self.assertEqual(cookie, 'cookievalue')

    def test_get_cookie_no_host(self):
        """If we request a cookie from another host, we shouldn't get a cookie."""
        self._create_login_cookie(self.tmpdir, 'https://example.com/',
                'userid', 'cookie')
        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(self.tmpdir,
                'https://bugzilla.mozilla.org')

        self.assertIsNone(userid)
        self.assertIsNone(cookie)

    def test_get_cookie_multiple_paths(self):
        """If we have multiple cookies for a domain, one with correct path is used."""
        self._create_login_cookie(self.tmpdir,
            'https://bugzilla.mozilla.org/production/', 'produser', 'prodpass')
        self._create_login_cookie(self.tmpdir,
            'https://bugzilla.mozilla.org/testing/', 'testuser', 'testpass')

        userid, cookie = auth.get_bugzilla_login_cookie_from_profile(self.tmpdir,
                'https://bugzilla.mozilla.org/testing/')
        self.assertEqual(userid, 'testuser')
        self.assertEqual(cookie, 'testpass')
