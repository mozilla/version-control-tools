# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import sys

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
    except:
        print >>sys.stderr, "Could not connect to the LDAP server at %s" % ldap_url
        sys.exit(1)


def get_ldap_attribute(mail, attr, conn_string):
    ldap_conn = ldap_connect(conn_string)
    if ldap_conn:
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
            if result[0][1].has_key(attr):
                attr_val = result[0][1][attr][0]
                ldap_conn.unbind_s()
                return attr_val
            else:
                ldap_conn.unbind_s()
                return False
    else:
        print >>sys.stderr, 'Don\'t have a valid ldap connection'
