import ldap

LDAP_HOST = 'ldap.db.scl3.mozilla.com'
LDAP_PORT = 389

def read_credentials():
    user, passwd = open('ldap-credentials.txt').read().strip().split(',')
    return (user, passwd)

def check_group(auth, group, email):
    try:
        l = ldap.initialize('ldap://%s:%s' % (LDAP_HOST, LDAP_PORT))
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s('uid=%s,ou=logins,dc=mozilla' % auth[0], auth[1])
        l.search('dc=mozilla', ldap.SCOPE_SUBTREE,
                  filterstr='cn=%s' % group)
        result = l.result(timeout=10)
        return email in result[1][0][1]['memberUid']
    except ldap.SERVER_DOWN, ldap.TIMEOUT:
        pass
