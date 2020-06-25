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
                    key_filename=None, scm_level=None, hg_access=True,
                    hg_enabled=True, bugzilla_email=None, groups=None):
        """Create a new user in LDAP.

        The user has an ``email`` address, a full ``name``, a
        ``username`` (for system accounts) and a numeric ``uid``.
        """

        if not bugzilla_email:
            bugzilla_email = email

        dn = 'mail=%s,o=com,dc=mozilla' % email

        username = username.encode('utf-8')
        fullname = fullname.encode('utf-8')
        bugzilla_email = bugzilla_email.encode('utf-8')

        r = [
            ('objectClass', [
                b'inetOrgPerson',
                b'organizationalPerson',
                b'person',
                b'posixAccount',
                b'bugzillaAccount',
                b'top',
            ]),
            ('cn', [fullname]),
            ('gidNumber', [b'100']),
            ('homeDirectory', [b'/home/%s' % username]),
            ('sn', [fullname.split()[-1]]),
            ('uid', [username]),
            ('uidNumber', [str(uid).encode('utf-8')]),
            ('bugzillaEmail', [bugzilla_email]),
        ]

        if hg_access:
            r[0][1].append(b'hgAccount')
            value = b'TRUE' if hg_enabled else b'FALSE'
            r.extend([
                ('fakeHome', [b'/tmp']),
                ('hgAccountEnabled', [value]),
                ('hgHome', [b'/tmp']),
                ('hgShell', [b'/bin/sh']),
            ])

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
            if scm_level < 1 or scm_level > 4:
                raise ValueError('scm level must be between 1 and 3 (or 4 for '
                                 '`scm_allow_direct_push`): %s' %
                                 scm_level)

            for level in range(1, scm_level + 1):
                if level == 4:
                    group = 'scm_allow_direct_push'
                else:
                    group = 'scm_level_%d' % level

                self.add_user_to_group(email, group)
                res['ldap_groups'].add(group)

        if groups:
            for group in groups:
                self.add_user_to_group(email, group)
                res['ldap_groups'].add(group)

        return res

    def delete_user(self, email):
        """ Deletes the specified user from LDAP. """
        dn = 'mail=%s,o=com,dc=mozilla' % email

        # Remove from posix groups.
        results = self.c.search_s(
            'ou=groups,dc=mozilla', ldap.SCOPE_SUBTREE,
            '(memberUid=%s)' % email, [b'cn'])
        for result in results:
            self.c.modify_s(result[0],
                            [(ldap.MOD_DELETE, b'memberUid', str(email))])

        # Remove from ldap groups.
        results = self.c.search_s(
            'ou=groups,dc=mozilla', ldap.SCOPE_SUBTREE,
            '(member=%s)' % dn, [b'cn'])
        for result in results:
            self.c.modify_s(result[0],
                            [(ldap.MOD_DELETE, b'member', str(dn))])

        # Delete the user entry.
        self.c.delete_s(dn)

    def create_vcs_sync_login(self, pubkey):
        dn = 'uid=vcs-sync,ou=logins,dc=mozilla'

        r = [
            ('objectClass', [
                b'account',
                b'top',
                b'uidObject',
                b'hgAccount',
                b'mailObject',
                b'posixAccount',
                b'ldapPublicKey',
            ]),
            ('cn', [b'VCS Sync']),
            ('fakeHome', [b'/tmp']),
            ('gidNumber', [b'100']),
            ('hgAccountEnabled', [b'TRUE']),
            ('hgHome', [b'/tmp']),
            ('hgShell', [b'/bin/sh']),
            ('homeDirectory', [b'/home/vcs-sync']),
            ('mail', [b'vcs-sync@mozilla.com']),
            ('uidNumber', [b'1500']),
            ('sshPublicKey', [pubkey.encode('utf-8')]),
        ]

        self.c.add_s(dn, r)

    def add_ssh_key(self, email, key):
        """Add an SSH key to a user in LDAP."""
        dn = 'mail=%s,o=com,dc=mozilla' % email

        modlist = []

        try:
            existing = self.c.search_s(dn, ldap.SCOPE_BASE)[0][1]
            if b'ldapPublicKey' not in existing['objectClass']:
                modlist.append((ldap.MOD_ADD, 'objectClass', b'ldapPublicKey'))
        except ldap.NO_SUCH_OBJECT:
            pass

        modlist.append((ldap.MOD_ADD, 'sshPublicKey', key))

        self.c.modify_s(dn, modlist)

    def add_user_to_group(self, email, group):
        """Add a user to the specified LDAP group.

        The ``group`` is defined in terms of its ``cn`` under
        ``ou=groups,dc=mozilla`. e.g. ``scm_level_3``.
        """
        dn = 'mail=%s,o=com,dc=mozilla' % email

        group_dn = 'cn=%s,ou=groups,dc=mozilla' % group
        modlist = [(ldap.MOD_ADD, 'memberUid', email.encode('utf-8'))]
        self.c.modify_s(group_dn, modlist)

        # MoCo LDAP has an active_* for each scm_level_* group, which we need
        # to emulate here.
        if group.startswith('scm_'):
            group_dn = 'cn=active_%s,ou=groups,dc=mozilla' % group
            modlist = [(ldap.MOD_ADD, 'member', dn.encode('utf-8'))]
            self.c.modify_s(group_dn, modlist)
