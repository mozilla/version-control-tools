#require docker

  $ . $TESTDIR/scripts/pash/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-ldap-user user@example.com testuser 1000 'Test User' --key-file testuser

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com
  > EOF

We are able to clone via SSH

  $ hgmo create-repo repo1 1
  $ hg clone ssh://$SSH_SERVER:$HGPORT/repo1
  remote: Warning: Permanently added '[*]:$HGPORT' (RSA) to the list of known hosts. (glob)
  destination directory: repo1
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Invalid paths are rejected

  $ hg clone ssh://$SSH_SERVER:$HGPORT/foo/../../etc/password
  remote: Only alpha-numeric characters, ".", and "-" are allowed in the repository names.
  remote: Please try again with only those characters.
  abort: no suitable response from remote hg!
  [255]

  $ hgmo clean
