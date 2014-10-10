# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os
import shutil
import tempfile
import time
import unittest

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
