# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this,
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

HOST_FINGERPRINTS = {
    'bitbucket.org': '3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa',
    'bugzilla.mozilla.org': '7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17',
    'hg.mozilla.org': 'af:27:b9:34:47:4e:e5:98:01:f6:83:2b:51:c9:aa:d8:df:fb:1a:27',
}


class MercurialConfig(object):
    """Interface for manipulating a Mercurial config file."""

    def add_mozilla_host_fingerprints(self):
        """Add host fingerprints so SSL connections don't warn."""
        if 'hostfingerprints' not in self._c:
            self._c['hostfingerprints'] = {}

        for k, v in HOST_FINGERPRINTS.items():
            self._c['hostfingerprints'][k] = v

    def update_mozilla_host_fingerprints(self):
        """Update host fingerprints if they are present."""
        if 'hostfingerprints' not in self._c:
            return

        for k, v in HOST_FINGERPRINTS.items():
            if k in self._c['hostfingerprints']:
                self._c['hostfingerprints'][k] = v

    def activate_extension(self, name, path=None):
        """Activate an extension.

        An extension is defined by its name (in the config) and a filesystem
        path). For built-in extensions, an empty path is specified.
        """
        if not path:
            path = ''

        if 'extensions' not in self._c:
            self._c['extensions'] = {}

        self._c['extensions'][name] = path

    def get_bugzilla_credentials(self):
        if 'bugzilla' not in self._c:
            return None, None, None, None, None

        b = self._c['bugzilla']
        return (
            b.get('username', None),
            b.get('password', None),
            b.get('userid', None),
            b.get('cookie', None),
            b.get('apikey', None),
        )

    def set_bugzilla_credentials(self, username, api_key):
        b = self._c.setdefault('bugzilla', {})
        if username:
            b['username'] = username
        if api_key:
            b['apikey'] = api_key

    def clear_legacy_bugzilla_credentials(self):
        if 'bugzilla' not in self._c:
            return

        b = self._c['bugzilla']
        for k in ('password', 'userid', 'cookie'):
            if k in b:
                del b[k]

    def have_wip(self):
        return 'wip' in self._c.get('alias', {})

    def install_wip_alias(self):
        """hg wip shows a concise view of work in progress."""
        alias = self._c.setdefault('alias', {})
        alias['wip'] = 'log --graph --rev=wip --template=wip'

        revsetalias = self._c.setdefault('revsetalias', {})
        revsetalias['wip'] = ('('
                'parents(not public()) '
                'or not public() '
                'or . '
                'or (head() and branch(default))'
            ') and (not obsolete() or unstable()^) '
            'and not closed()')

        templates = self._c.setdefault('templates', {})
        templates['wip'] = ("'"
            # prefix with branch name
            '{label("log.branch", branches)} '
            # rev:node
            '{label("changeset.{phase}", rev)}'
            '{label("changeset.{phase}", ":")}'
            '{label("changeset.{phase}", short(node))} '
            # just the username part of the author, for brevity
            '{label("grep.user", author|user)}'
            # tags and bookmarks
            '{label("log.tag", if(tags," {tags}"))}'
            '{label("log.tag", if(fxheads," {fxheads}"))} '
            '{label("log.bookmark", if(bookmarks," {bookmarks}"))}'
            '\\n'
            # first line of commit message
            '{label(ifcontains(rev, revset("."), "desc.here"),desc|firstline)}'
            "'"
        )
