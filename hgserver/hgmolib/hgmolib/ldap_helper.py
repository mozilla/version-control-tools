# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import sys
import datetime

import ldap


def get_ldap_settings():
    """Read LDAP settings from a file."""
    with open('/etc/mercurial/ldap.json', 'rb') as fh:
        return json.load(fh)


def ldap_connect(ldap_url):
    try:
        settings = get_ldap_settings()
        ldap_conn = ldap.initialize(ldap_url)

        if settings.get('starttls', True):
            ldap_conn.start_tls_s()

        ldap_conn.simple_bind_s(settings['username'], settings['password'])
        return ldap_conn
    except Exception:
        print >>sys.stderr, "Could not connect to the LDAP server at %s" % ldap_url
        return None


def get_ldap_attribute(mail, attr, conn_string):
    ldap_conn = ldap_connect(conn_string)
    if not ldap_conn:
        # This is a bit hacky. Ideally we'd have proper exception
        # handling everywhere.
        sys.exit(1)

    result = ldap_conn.search_s('dc=mozilla', ldap.SCOPE_SUBTREE, '(mail=' + mail + ')', [attr])
    if len(result) > 1:
        print >>sys.stderr, 'More than one match found'
        ldap_conn.unbind_s()
        return False
    elif len(result) == 0:
        print >>sys.stderr, 'No matches found'
        ldap_conn.unbind_s()
        return False
    else:
        if attr in result[0][1]:
            attr_val = result[0][1][attr][0]
            ldap_conn.unbind_s()
            return attr_val
        else:
            ldap_conn.unbind_s()
            return False


def update_access_date(mail, attr, value, conn_string_ro,
                          conn_string_write):
    ldap_conn_ro = ldap_connect(conn_string_ro)
    ldap_conn_write = ldap_connect(conn_string_write)
    entry_filter = '(&(mail=' + mail + ')(hgAccountEnabled=TRUE))'

    if not ldap_conn_ro or not ldap_conn_write:
        return

    results = ldap_conn_ro.search_s('dc=mozilla', ldap.SCOPE_SUBTREE,
                                    entry_filter, [attr, 'objectClass'])
    if not results:
        return

    dn, old_entry = results[0]

    # Only update attribute for accounts belonging to the hgAccount object
    # class.
    if 'hgAccount' not in old_entry['objectClass']:
        return

    now = datetime.datetime.utcnow()
    yesterday = now - datetime.timedelta(days=1)

    try:
        last_access = datetime.datetime.strptime(old_entry[attr][0],
                                                 '%Y%m%d%H%M%S.%fZ')

    # Old values don't have partial second time.
    except ValueError:
        last_access = datetime.datetime.strptime(old_entry[attr][0],
                                                 '%Y%m%d%H%M%SZ')
    # Attribute not yet set.
    except KeyError:
        # Default to something very old. ~20 years.
        last_access = now - datetime.timedelta(days=7300)

    if last_access < yesterday:
        ldap_conn_write.modify_s(dn, [(ldap.MOD_REPLACE, attr, value)])


def get_user_dn_by_mail(conn, ldap_basedn, email):
    try:
        user_obj = conn.search_s(
            ldap_basedn,
            ldap.SCOPE_SUBTREE,
            '(mail=%s)' % email
        )
        return user_obj[0][0]
    except (IndexError, ldap.NO_SUCH_OBJECT):
        return None


def get_scm_groups(mail):
    """Obtain SCM LDAP group membership for a specified user."""
    settings = get_ldap_settings()
    conn = ldap_connect(settings['url'])
    if not conn:
        return None

    fltr = '(&(cn=scm_*)(memberUid=%s))' % mail

    result = conn.search_s('ou=groups,dc=mozilla', ldap.SCOPE_ONELEVEL,
                           fltr, ['cn'])

    groups = set()
    for dn, attrs in result:
        for group in attrs['cn']:
            groups.add(group)

    return groups


def get_active_scm_groups(mail):
    """Obtain active SCM LDAP group membership for a specified user."""
    settings = get_ldap_settings()
    conn = ldap_connect(settings['url'])
    if not conn:
        return None

    dn = get_user_dn_by_mail(conn, 'dc=mozilla', mail)
    fltr = '(&(cn=active_scm_*)(member=%s))' % dn

    result = conn.search_s('ou=groups,dc=mozilla', ldap.SCOPE_ONELEVEL,
                           fltr, ['cn'])

    groups = set()
    for dn, attrs in result:
        for group in attrs['cn']:
            groups.add(group)

    return groups
