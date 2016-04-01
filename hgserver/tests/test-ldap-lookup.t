#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ alias lookup="hgmo exec hgssh /var/hg/version-control-tools/scripts/ldap-lookup-ssh-key"

No arguments prints error

  $ lookup
  usage: /var/hg/version-control-tools/scripts/ldap-lookup-ssh-key <user>
  [1]

Multiple arguments prints failure

  $ lookup me you
  usage: /var/hg/version-control-tools/scripts/ldap-lookup-ssh-key <user>
  [1]

Looking up unknown user prints failure

  $ lookup nobody@nowhere.com
  user not found
  [1]

User with no SSH key has failure

  $ hgmo create-ldap-user user1@example.com user1 1000 'Some User'
  $ lookup user1@example.com
  no SSH keys found for user
  [1]

User with single SSH key has key printed

  $ ssh-keygen -b 2048 -t rsa -f key1 -N '' > /dev/null
  $ hgmo add-ssh-key user1@example.com - < key1.pub

  $ lookup user1@example.com
  ssh-rsa * (glob)

Multiple keys are printed

  $ ssh-keygen -b 2048 -t rsa -f key2 -N '' > /dev/null
  $ hgmo add-ssh-key user1@example.com - < key2.pub

  $ lookup user1@example.com
  ssh-rsa * (glob)
  ssh-rsa * (glob)

DSA keys are filtered

  $ hgmo create-ldap-user dsauser@example.com dsauser 1001 'DSA User'
  $ ssh-keygen -t dsa -f dsakey -N '' > /dev/null
  $ hgmo add-ssh-key dsauser@example.com - < dsakey.pub

  $ lookup dsauser@example.com
  no valid SSH keys found for user
  [1]

  $ hgmo add-ssh-key dsauser@example.com - < key1.pub
  $ lookup dsauser@example.com
  ssh-rsa * (glob)

  $ hgmo clean
