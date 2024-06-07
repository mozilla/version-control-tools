#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-ldap-user user@example.com testuser 1000 'Test User' --key-file testuser --scm-level 1

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com
  > EOF

  $ alias hgssh="ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com -p $HGPORT"

We are able to clone via SSH

  $ hgmo create-repo repo1 scm_level_1
  (recorded repository creation in replication log)
  $ hg clone ssh://$SSH_SERVER:$HGPORT/repo1
  destination directory: repo1
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Invalid paths are rejected

  $ hg clone ssh://$SSH_SERVER:$HGPORT/foo/../../etc/password
  remote: Only alpha-numeric characters, ".", "_", and "-" are allowed in repository
  remote: names.  Additionally the first character of repository names must be alpha-numeric.
  abort: no suitable response from remote hg
  [255]

A push works

  $ cd repo1
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push ssh://$SSH_SERVER:$HGPORT/repo1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/repo1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/repo1/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Trailing slash works

  $ hg push ssh://$SSH_SERVER:$HGPORT/repo1/
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/repo1/
  searching for changes
  no changes found
  [1]

Various hg command invocations aren't allowed

  $ hgssh ${SSH_SERVER} hg serve
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} foohg repo1
  A SSH connection has been successfully established.
  
  Your account (user@example.com) has privileges to access Mercurial over
  SSH.
  
  The command you specified is not allowed on this server.
  
  Goodbye.
  [1]

  $ hgssh ${SSH_SERVER} hg -R repo1 log
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R repo1 serve --debugger
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R repo1 serve --stdio --debugger
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R repo1 serve --config ui.test=foo --stdio --debugger
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R repo 1 serve --stdio
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R "repo 1" serve --stdio
  invalid `hg` command executed; can only run serve --stdio
  [1]

  $ hgssh ${SSH_SERVER} hg -R \'repo 1\' serve --stdio
  Only alpha-numeric characters, ".", "_", and "-" are allowed in repository
  names.  Additionally the first character of repository names must be alpha-numeric.
  [1]

  $ hgssh ${SSH_SERVER} hg -R \"repo 1\" serve --stdio
  Only alpha-numeric characters, ".", "_", and "-" are allowed in repository
  names.  Additionally the first character of repository names must be alpha-numeric.
  [1]

Cleanup

  $ hgmo clean
