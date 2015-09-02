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
        ldap_conn.simple_bind_s(settings['username'], settings['password'])
        return ldap_conn
    except Exception:
        print >>sys.stderr, "Could not connect to the LDAP server at %s" % ldap_url
        sys.exit(1)


def get_ldap_attribute(mail, attr, conn_string):
    ldap_conn = ldap_connect(conn_string)
    if ldap_conn:
        result = ldap_conn.search_s('dc=mozilla', ldap.SCOPE_SUBTREE, '(mail=' + mail + ')', [attr])
        if (len(result) > 1):
            print >>sys.stderr, 'More than one match found'
            ldap_conn.unbind_s()
            return False
        elif (len(result) == 0):
            print >>sys.stderr, 'No matches found'
            ldap_conn.unbind_s()
            return False
        else:
            if result[0][1].has_key(attr):
                attr_val = result[0][1][attr][0]
                ldap_conn.unbind_s()
                return attr_val
            else:
                ldap_conn.unbind_s()
                return False
    else:
        print >>sys.stderr, 'Don\'t have a valid ldap connection'


def update_ldap_attribute(mail, attr, value, conn_string_ro, conn_string_write):
    ldap_conn_ro = ldap_connect(conn_string_ro)
    ldap_conn_write = ldap_connect(conn_string_write)
    entry_filter = '(&(mail=' + mail + ')(hgAccountEnabled=TRUE))'

    if not ldap_conn_ro or not ldap_conn_write:
        return

    results = ldap_conn_ro.search_s('dc=mozilla', ldap.SCOPE_SUBTREE,
                                    entry_filter, [attr])
    if not results:
        return

    (dn, old_entry) = results[0]
    if results[0][1].has_key(attr):
        try:
            access_time = datetime.datetime.strptime(results[0][1][attr][0], "%Y%m%d%H%M%SZ")
        except ValueError:
            access_time = datetime.datetime.strptime(results[0][1][attr][0], "%Y%m%d%H%M%S.%fZ")
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        if access_time < yesterday:
            ldap_conn_write.modify_s(dn, [(ldap.MOD_REPLACE, attr, value)])
    else:
        raise Exception()
