import ldap
import mozdef

LDAP_HOST = 'ldap.mozilla.org'
LDAP_PORT = 636


def read_credentials():
    user, passwd = open('credentials/ldap.txt').read().strip().split(',')
    return (user, passwd)


def check_group(auth, group, email):
    try:
        l = ldap.initialize('ldaps://%s:%s' % (LDAP_HOST, LDAP_PORT))
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s('uid=%s,ou=logins,dc=mozilla' % auth[0], auth[1])
        l.search('dc=mozilla', ldap.SCOPE_SUBTREE,
                 filterstr='cn=%s' % group)
        result = l.result(timeout=10)
        in_group = email in result[1][0][1]['memberUid']
        mozdef_auth = mozdef.read_credentials()
        mozdef.post_ldap_group_check(mozdef_auth, email, group, in_group)
        return in_group
    except ldap.SERVER_DOWN, ldap.TIMEOUT:
        pass
