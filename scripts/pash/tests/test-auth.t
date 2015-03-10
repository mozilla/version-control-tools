#require docker

  $ . $TESTDIR/scripts/pash/tests/helpers.sh
  $ hgmoenv

Attempting to SSH into pash as an unknown user is denied

  $ ssh-keygen -b 2048 -t rsa -f key1 -N '' > /dev/null

  $ testssh -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  Warning: Permanently added '[*]:$HGPORT' (RSA) to the list of known hosts.\r (glob) (esc)
  Permission denied (publickey).\r (esc)
  [255]

SSH as a valid user without proper key

  $ hgmo create-ldap-user user1@example.com user1 1000 'Some User'
  $ testssh -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  Permission denied (publickey).\r (esc)
  [255]

SSH with a valid key gives us warning about no interactive shells

  $ hgmo add-ssh-key user1@example.com - < key1.pub
  $ testssh -i key1 -l user1@example.com -p $HGPORT $SSH_SERVER
  No interactive shells allowed here!
  [1]

  $ hgmo clean
