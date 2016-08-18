#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

  $ hgmo create-repo obs scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option obs phases publish false
  $ hgmo exec hgssh /set-hgrc-option obs experimental evolution all
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs replicatehgrc
  recorded hgrc in replication log

  $ consumer --onetime
  $ consumer --onetime
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer writing hgrc: $TESTTMP/repos/obs/.hg/hgrc

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/obs client
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase =
  > [experimental]
  > evolution = all
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -f -r .
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/77538e1ce4be
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs

Pruning a changeset locally and pushing should result in obsolescence marker on server

  $ touch file0
  $ hg -q commit -A -m 'add file0'
  $ touch file1
  $ hg -q commit -A -m 'add file1'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/442ce5a124e0
  remote:   https://hg.mozilla.org/obs/rev/11bec8a6b2a3
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  vcsreplicator.consumer pulling 1 heads (11bec8a6b2a30ac170575ecfd7a06af5a75e2d77) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs

  $ hg -q up -r 1
  $ touch file2
  $ hg -q commit -A -m 'add file2'
  $ hg rebase -s 2 -d .
  rebasing 2:11bec8a6b2a3 "add file1"

  $ hg debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to 2 files (+1 heads)
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/5dfb8fc50086
  remote:   https://hg.mozilla.org/obs/rev/67b45555a21f
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Obsolescence marker should exist on master

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

Changegroup message written

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    heads:
    - 67b45555a21f4d9d470adc4f1ed3af63918f6414
    name: hg-changegroup-2
    nodecount: 2
    path: '{moz}/obs'
    source: serve

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  vcsreplicator.consumer pulling 1 heads (67b45555a21f4d9d470adc4f1ed3af63918f6414) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs

Obsolescence marker should have been replicated to hgweb

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

Creating obsolescence marker directly on server will result in replication
TODO this does not work

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete 67b45555a21f4d9d470adc4f1ed3af63918f6414
  no username found, using 'root@*' instead (glob)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'root@*'} (glob)

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

Cleanup

  $ hgmo clean
