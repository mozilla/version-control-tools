#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Attempting to SSH into pash as an unknown user is denied

  $ ssh-keygen -b 2048 -t rsa -f key1 -N '' > /dev/null

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  *Permission denied (publickey)* (glob)
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
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: bugzillaAccount
  objectClass: top
  objectClass: hgAccount
  cn: Some User
  gidNumber: 100
  homeDirectory: /home/user1
  sn: User
  uid: user1
  uidNumber: 1000
  bugzillaEmail: user1@example.com
  fakeHome: /tmp
  hgAccountEnabled: TRUE
  hgHome: /tmp
  hgShell: /bin/sh
  mail: user1@example.com
  
  # search result
  search: 2
  result: 0 Success
  
  # numResponses: 2
  # numEntries: 1

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  *Permission denied (publickey)* (glob)
  [255]

SSH with a valid key gives us warning about no command. Also prints note about
lack of LDAP group membership.

  $ hgmo add-ssh-key user1@example.com - < key1.pub
  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  A SSH connection has been successfully established.
  
  Your account (user1@example.com) has privileges to access Mercurial over
  SSH.
  
  You are NOT a member of any LDAP groups that govern source control access.
  
  You will NOT be able to push to any repository until you have been granted
  commit access.
  
  See https://www.mozilla.org/about/governance/policies/commit/access-policy/ for
  more information.
  
  You did not specify a command to run on the server. This server only
  supports running specific commands. Since there is nothing to do, you
  are being disconnected.
  [1]

SSH with invalid command prints appropriate error message

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER foobar
  A SSH connection has been successfully established.
  
  Your account (user1@example.com) has privileges to access Mercurial over
  SSH.
  
  The command you specified is not allowed on this server.
  
  Goodbye.
  [1]

SCM LDAP group membership is printed with no-op login.

  $ hgmo add-user-to-group user1@example.com scm_autoland
  $ hgmo add-user-to-group user1@example.com scm_level_1
  $ hgmo add-user-to-group user1@example.com scm_level_2

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  A SSH connection has been successfully established.
  
  Your account (user1@example.com) has privileges to access Mercurial over
  SSH.
  
  You are a member of the following LDAP groups that govern source control
  access:
  
     scm_autoland, scm_level_1, scm_level_2
  
  This will give you write access to the following repos:
  
     Autoland (integration/autoland), Project Repos (projects/), Try, User Repos (users/)
  
  You will NOT have write access to the following repos:
  
     Firefox Repos (mozilla-central, releases/*), Localization Repos (releases/l10n/*, others)
  
  You did not specify a command to run on the server. This server only
  supports running specific commands. Since there is nothing to do, you
  are being disconnected.
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
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: bugzillaAccount
  objectClass: top
  objectClass: hgAccount
  objectClass: ldapPublicKey
  cn: Some User
  gidNumber: 100
  homeDirectory: /home/user1
  sn: User
  uid: user1
  uidNumber: 1000
  bugzillaEmail: user1@example.com
  fakeHome: /tmp
  hgAccountEnabled: TRUE
  hgHome: /tmp
  hgShell: /bin/sh
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

Successful autoland login should set requester's hgAccountEnabled as well

bind-autoland account
  $ ssh-keygen -b 2048 -t rsa -f keyA -N '' > /dev/null
  $ hgmo create-ldap-user --key-file keyA bind-autoland@mozilla.com bind-autoland 1001 'bind-autoland'
  $ hgmo add-user-to-group bind-autoland@mozilla.com scm_autoland
  $ hgmo add-ssh-key bind-autoland@mozilla.com - < keyA.pub

user2
  $ hgmo create-ldap-user user2@example.com user2 1002 'other user'

ssh as autoland, tagging user2 as the originator of the request
  $ AUTOLAND_REQUEST_USER=user2@example.com ssh -T -F ssh_config -i keyA -l bind-autoland@mozilla.com -p $HGPORT $SSH_SERVER -o SendEnv=AUTOLAND_REQUEST_USER
  A SSH connection has been successfully established.
  
  Your account (bind-autoland@mozilla.com) has privileges to access Mercurial over
  SSH.
  
  You are a member of the following LDAP groups that govern source control
  access:
  
     scm_autoland
  
  This will give you write access to the following repos:
  
     Autoland (integration/autoland)
  
  You will NOT have write access to the following repos:
  
     Firefox Repos (mozilla-central, releases/*), Localization Repos (releases/l10n/*, others), Project Repos (projects/), Try, User Repos (users/)
  
  You did not specify a command to run on the server. This server only
  supports running specific commands. Since there is nothing to do, you
  are being disconnected.
  [1]

hgAccessDate on both accounts should be set
  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=bind-autoland@mozilla.com -LLL hgAccessDate
  dn: mail=bind-autoland@mozilla.com,o=com,dc=mozilla
  hgAccessDate: 2\d{3}\d{2}\d{2}\d{2}\d{2}\d{2}\.\d+Z (re)
  
  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=user2@example.com -LLL hgAccessDate
  dn: mail=user2@example.com,o=com,dc=mozilla
  hgAccessDate: 2\d{3}\d{2}\d{2}\d{2}\d{2}\d{2}\.\d+Z (re)
  

No HG access prints helpful error message

  $ hgmo create-ldap-user --no-hg-access --key-file key1 nohgaccess@example.com nohgaccess 1001 'No HgAccess'
  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=nohgaccess@example.com
  # extended LDIF
  #
  # LDAPv3
  # base <dc=mozilla> with scope subtree
  # filter: mail=nohgaccess@example.com
  # requesting: ALL
  #
  
  # nohgaccess@example.com, com, mozilla
  dn: mail=nohgaccess@example.com,o=com,dc=mozilla
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: bugzillaAccount
  objectClass: top
  objectClass: ldapPublicKey
  cn: No HgAccess
  gidNumber: 100
  homeDirectory: /home/nohgaccess
  sn: HgAccess
  uid: nohgaccess
  uidNumber: 1001
  bugzillaEmail: nohgaccess@example.com
  mail: nohgaccess@example.com
  sshPublicKey:* (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
  
  # search result
  search: 2
  result: 0 Success
  
  # numResponses: 2
  # numEntries: 1

  $ ssh -T -F ssh_config -i key1 -l nohgaccess@example.com -p $HGPORT $SSH_SERVER
  Could not chdir to home directory : No such file or directory
  A SSH connection has been established and your account (nohgaccess@example.com)
  was found in LDAP.
  
  However, Mercurial access is not currently enabled on your LDAP account.
  
  Please follow the instructions at the following URL to gain Mercurial
  access:
  
      https://www.mozilla.org/en-US/about/governance/policies/commit/

Do another login to verify no pash errors are present

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  A SSH connection has been successfully established.
  
  Your account (user1@example.com) has privileges to access Mercurial over
  SSH.
  
  You are a member of the following LDAP groups that govern source control
  access:
  
     scm_autoland, scm_level_1, scm_level_2
  
  This will give you write access to the following repos:
  
     Autoland (integration/autoland), Project Repos (projects/), Try, User Repos (users/)
  
  You will NOT have write access to the following repos:
  
     Firefox Repos (mozilla-central, releases/*), Localization Repos (releases/l10n/*, others)
  
  You did not specify a command to run on the server. This server only
  supports running specific commands. Since there is nothing to do, you
  are being disconnected.
  [1]

  $ hgmo exec hgssh cat /var/log/pash.log

hgAccountEnabled=FALSE shows account disabled message

  $ hgmo create-ldap-user --hg-disabled --key-file key1 hgdisabled@example.com hgdisabled 1002 'HgAccess Disabled'
  $ hgmo exec hgssh /usr/bin/ldapsearch -b 'dc=mozilla' -s sub -x mail=hgdisabled@example.com
  # extended LDIF
  #
  # LDAPv3
  # base <dc=mozilla> with scope subtree
  # filter: mail=hgdisabled@example.com
  # requesting: ALL
  #
  
  # hgdisabled@example.com, com, mozilla
  dn: mail=hgdisabled@example.com,o=com,dc=mozilla
  objectClass: inetOrgPerson
  objectClass: organizationalPerson
  objectClass: person
  objectClass: posixAccount
  objectClass: bugzillaAccount
  objectClass: top
  objectClass: hgAccount
  objectClass: ldapPublicKey
  cn: HgAccess Disabled
  gidNumber: 100
  homeDirectory: /home/hgdisabled
  sn: Disabled
  uid: hgdisabled
  uidNumber: 1002
  bugzillaEmail: hgdisabled@example.com
  fakeHome: /tmp
  hgAccountEnabled: FALSE
  hgHome: /tmp
  hgShell: /bin/sh
  mail: hgdisabled@example.com
  sshPublicKey:: * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
   * (glob)
  
  # search result
  search: 2
  result: 0 Success
  
  # numResponses: 2
  # numEntries: 1

  $ ssh -T -F ssh_config -i key1 -l hgdisabled@example.com -p $HGPORT $SSH_SERVER
  A SSH connection has been established, your account (hgdisabled@example.com)
  was found in LDAP, and your account has been configured for Mercurial
  access.
  
  However, Mercurial access is currently disabled on your account.
  This commonly occurs due to account inactivity (you need to SSH
  into hg.mozilla.org every few months to keep your account active).
  
  To restore Mercurial access, please file a MOC Service Request
  bug (http://tinyurl.com/njcfhma) and request hg access be restored
  for hgdisabled@example.com.

mozreview-ldap-associate isn't enabled on hgssh

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER mozreview-ldap-associate
  mozreview-ldap-associate command not available
  [1]

Failure to connect to LDAP mirror locks us out
What happens here is nscd caches the valid passwd entry lookup for the user.
However, the SSH key lookup via LDAP fails and this manifests as no public keys
available.

  $ hgmo exec hgssh /set-ldap-property url ldap://localhost:6000
  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  *Permission denied (publickey)* (glob)
  [255]

  $ hgmo exec hgssh /set-ldap-property url real

Failure to connect to LDAP master server is not fatal

  $ hgmo exec hgssh /set-ldap-property write_url ldap://localhost:6000

  $ ssh -T -F ssh_config -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  Could not connect to the LDAP server at ldap://localhost:6000
  A SSH connection has been successfully established.
  
  Your account (user1@example.com) has privileges to access Mercurial over
  SSH.
  
  You are a member of the following LDAP groups that govern source control
  access:
  
     scm_autoland, scm_level_1, scm_level_2
  
  This will give you write access to the following repos:
  
     Autoland (integration/autoland), Project Repos (projects/), Try, User Repos (users/)
  
  You will NOT have write access to the following repos:
  
     Firefox Repos (mozilla-central, releases/*), Localization Repos (releases/l10n/*, others)
  
  You did not specify a command to run on the server. This server only
  supports running specific commands. Since there is nothing to do, you
  are being disconnected.
  [1]

Can pull when LDAP master is not available

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)
  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F `pwd`/ssh_config -i `pwd`/key1 -l user1@example.com
  > EOF

  $ hg clone ssh://${SSH_SERVER}:${HGPORT}/mozilla-central
  remote: Could not connect to the LDAP server at ldap://localhost:6000
  destination directory: mozilla-central
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hgmo exec hgssh /set-ldap-property write_url real

Cleanup

  $ hgmo clean
