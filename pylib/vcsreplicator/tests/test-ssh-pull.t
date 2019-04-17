#require hgmodocker vcsreplicator

This test demonstrates the pull behaviour on hgssh servers

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ scm3user

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option mozilla-central phases publish false
  $ hgmo exec hgssh /set-hgrc-option mozilla-central experimental evolution all
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central client
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central client2

  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase =
  > [experimental]
  > evolution = all
  > [ui]
  > ssh = ssh -F $TESTTMP/ssh_config -i $TESTTMP/l3user -l l3user@example.com
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -f -r .
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ touch file0
  $ hg -q commit -A -m 'add file0'
  $ touch file1
  $ hg -q commit -A -m 'add file1'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/442ce5a124e001862e8bd6a8871d8b85e09bebd7
  remote:   https://hg.mozilla.org/mozilla-central/rev/11bec8a6b2a30ac170575ecfd7a06af5a75e2d77
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ hg -q up -r 1
  $ touch file2
  $ hg -q commit -A -m 'add file2'
  $ hg rebase -s 2 -d .
  rebasing 2:11bec8a6b2a3 "add file1"

  $ hg debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)

  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to 2 files (+1 heads)
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/5dfb8fc50086c183d1cbd067e48c58307db16dac
  remote:   https://hg.mozilla.org/mozilla-central/rev/67b45555a21f4d9d470adc4f1ed3af63918f6414
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

State of repo on ssh server

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/mozilla-central --hidden log -G
  o  changeset:   4:67b45555a21f
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file1
  |
  o  changeset:   3:5dfb8fc50086
  |  parent:      1:442ce5a124e0
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file2
  |
  | x  changeset:   2:11bec8a6b2a3
  |/   user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    rewritten using rebase as 4:67b45555a21f by Test User <someone@example.com>
  |    summary:     add file1
  |
  o  changeset:   1:442ce5a124e0
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file0
  |
  o  changeset:   0:77538e1ce4be
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  
State of repo on pushing users machine

  $ hg --hidden log -G
  o  changeset:   4:67b45555a21f
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file1
  |
  @  changeset:   3:5dfb8fc50086
  |  parent:      1:442ce5a124e0
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file2
  |
  | x  changeset:   2:11bec8a6b2a3
  |/   user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    rewritten using rebase as 4:67b45555a21f
  |    summary:     add file1
  |
  o  changeset:   1:442ce5a124e0
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file0
  |
  o  changeset:   0:77538e1ce4be
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  
  $ cd ..
  $ cd client2
  $ hg pull
  pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 4 files
  new changesets 77538e1ce4be:67b45555a21f (3 drafts)
  (run 'hg update' to get a working copy)

State of repo on pulling users machine.

  $ hg --hidden log -G
  o  changeset:   3:67b45555a21f
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file1
  |
  o  changeset:   2:5dfb8fc50086
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file2
  |
  o  changeset:   1:442ce5a124e0
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add file0
  |
  o  changeset:   0:77538e1ce4be
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  
