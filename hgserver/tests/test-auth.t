#require docker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Attempting to SSH into pash as an unknown user is denied

  $ ssh-keygen -b 2048 -t rsa -f key1 -N '' > /dev/null

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  Permission denied (publickey).\r (esc)
  [255]

SSH as a valid user without proper key

  $ hgmo create-ldap-user user1@example.com user1 1000 'Some User'
  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=user1@example.com
  # extended LDIF
  #
  # LDAPv3
  # base <dc=mozilla> with scope subtree
  # filter: mail=user1@example.com
  # requesting: ALL
  #
  
  # user1@example.com, com, mozilla
  dn: mail=user1@example.com,o=com,dc=mozilla
  objectClass: hgAccount
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: top
  cn: Some User
  fakeHome: /tmp
  gidNumber: 100
  hgAccountEnabled: TRUE
  hgHome: /tmp
  hgShell: /bin/sh
  homeDirectory: /home/user1
  sn: User
  uid: user1
  uidNumber: 1000
  mail: user1@example.com
  
  # search result
  search: 2
  result: 0 Success
  
  # numResponses: 2
  # numEntries: 1

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  Permission denied (publickey).\r (esc)
  [255]

SSH with a valid key gives us warning about no interactive shells

  $ hgmo add-ssh-key user1@example.com - < key1.pub
  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  No interactive shells allowed here!
  [1]

Successful login should set hgAccessDate LDAP attribute

  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=user1@example.com
  # extended LDIF
  #
  # LDAPv3
  # base <dc=mozilla> with scope subtree
  # filter: mail=user1@example.com
  # requesting: ALL
  #
  
  # user1@example.com, com, mozilla
  dn: mail=user1@example.com,o=com,dc=mozilla
  objectClass: hgAccount
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: top
  objectClass: ldapPublicKey
  cn: Some User
  fakeHome: /tmp
  gidNumber: 100
  hgAccountEnabled: TRUE
  hgHome: /tmp
  hgShell: /bin/sh
  homeDirectory: /home/user1
  sn: User
  uid: user1
  uidNumber: 1000
  mail: user1@example.com
  sshPublicKey: ssh-rsa * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
  hgAccessDate: 2\d{3}\d{2}\d{2}\d{2}\d{2}\d{2}\.\d+Z (re)
  
  # search result
  search: 2
  result: 0 Success
  
  # numResponses: 2
  # numEntries: 1

Do another login to verify no pash errors are present

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  No interactive shells allowed here!
  [1]

  $ hgmo exec hgssh cat /var/log/pash.log

  $ hgmo stop
