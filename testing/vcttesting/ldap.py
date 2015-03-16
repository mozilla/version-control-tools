# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import os

import ldap
import paramiko


class LDAP(object):
    """Interface to an LDAP server."""

    def __init__(self, uri, username=None, password=None):
        self.c = ldap.initialize(uri)

        if username and password:
            self.c.simple_bind_s(username, password)

    def create_user(self, email, username, uid, fullname,
                         key_filename=None, scm_level=None):
        """Create a new user in LDAP.

        The user has an ``email`` address, a full ``name``, a
        ``username`` (for system accounts) and a numeric ``uid``.
        """

        dn = 'mail=%s,o=com,dc=mozilla' % email

        r = [
            (b'objectClass', [
                b'hgAccount',
                b'inetOrgPerson',
                b'organizationalPerson',
                b'person',
                b'posixAccount',
                b'top',
            ]),
            (b'cn', [fullname]),
            (b'fakeHome', [b'/tmp']),
            (b'gidNumber', [b'100']),
            (b'hgAccountEnabled', [b'TRUE']),
            (b'hgHome', [b'/tmp']),
            (b'hgShell', [b'/bin/sh']),
            (b'homeDirectory', [b'/home/%s' % username]),
            (b'sn', [fullname.split()[-1]]),
            (b'uid', [username]),
            (b'uidNumber', [str(uid)]),
        ]

        self.c.add_s(dn, r)

        res = {
            'dn': dn,
            'ldap_groups': set(),
        }

        if key_filename:
            pubkey_filename = '%s.pub' % key_filename
            if os.path.exists(key_filename):
                with open(pubkey_filename, 'rb') as fh:
                    pubkey = fh.read()
            else:
                k = paramiko.rsakey.RSAKey.generate(2048)
                k.write_private_key_file(key_filename)
                pubkey = '%s %s %s' % (k.get_name(), k.get_base64(), email)
                pubkey = pubkey.encode('utf-8')
                with open(pubkey_filename, 'wb') as fh:
                    fh.write(pubkey)

            self.add_ssh_key(email, pubkey)
            res['ssh_pubkey'] = pubkey
            res['ssh_key_filename'] = key_filename
            res['ssh_pubkey_filename'] = pubkey_filename

        if scm_level:
            if scm_level < 1 or scm_level > 3:
                raise ValueError('scm level must be between 1 and 3: %s' %
                                 scm_level)

            for level in range(1, scm_level + 1):
                group = b'scm_level_%d' % level
                self.add_user_to_group(email, group)
                res['ldap_groups'].add(group)

        return res

    def create_vcs_sync_login(self, pubkey):
        dn = 'uid=vcs-sync,ou=logins,dc=mozilla'

        r = [
            (b'objectClass', [
                b'account',
                b'top',
                b'uidObject',
                b'hgAccount',
                b'mailObject',
                b'posixAccount',
                b'ldapPublicKey',
            ]),
            (b'cn', [b'VCS Sync']),
            (b'fakeHome', [b'/tmp']),
            (b'gidNumber', [b'100']),
            (b'hgAccountEnabled', [b'TRUE']),
            (b'hgHome', [b'/tmp']),
            (b'hgShell', [b'/bin/sh']),
            (b'homeDirectory', [b'/home/vcs-sync']),
            (b'mail', [b'vcs-sync@mozilla.com']),
            (b'uidNumber', [b'1500']),
            (b'sshPublicKey', [pubkey]),
        ]

        self.c.add_s(dn, r)

    def add_ssh_key(self, email, key):
        """Add an SSH key to a user in LDAP."""
        dn = 'mail=%s,o=com,dc=mozilla' % email

        modlist = []

        try:
            existing = self.c.search_s(dn, ldap.SCOPE_BASE)[0][1]
            if b'ldapPublicKey' not in existing[b'objectClass']:
                modlist.append((ldap.MOD_ADD, b'objectClass', b'ldapPublicKey'))
        except ldap.NO_SUCH_OBJECT:
            pass

        modlist.append((ldap.MOD_ADD, b'sshPublicKey', key))

        self.c.modify_s(dn, modlist)

    def add_user_to_group(self, member, group):
        """Add a user to the specified LDAP group.

        The ``group`` is defined in terms of its ``cn`` under
        ``ou=groups,dc=mozilla`. e.g. ``scml_level_3``.
        """
        dn = 'cn=%s,ou=groups,dc=mozilla' % group

        modlist = [(ldap.MOD_ADD, b'memberUid', member)]
        self.c.modify_s(dn, modlist)
