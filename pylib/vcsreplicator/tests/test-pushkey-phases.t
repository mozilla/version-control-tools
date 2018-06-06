#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create the repository and push a change

  $ hgmo exec hgssh /create-repo mozilla-central scm_level_1 --non-publishing
  (recorded repository creation in replication log)
  marking repo as non-publishing
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log
  $ standarduser
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central
  $ consumer --onetime
  vcsreplicator.consumer processing hg-hgrc-update-1 from partition 2 offset 1
  vcsreplicator.consumer writing hgrc: $TESTTMP/repos/mozilla-central/.hg/hgrc

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial

  $ hg log -T '{rev} {phase}\n'
  0 draft

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
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ hg log -T '{rev} {phase}\n'
  0 draft

There should be no pushkey on a push with a draft changeset

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 3
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 4
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 77538e1ce4be (hg44 !)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  0 draft

Locally bumping changeset to public will trigger a pushkey

  $ hg phase --public -r .
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  no changes found
  remote: recorded updates to phases in replication log in \d\.\d+s (re)
  [1]

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    key: 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-pushkey-1
    namespace: phases
    new: '0'
    old: '1'
    path: '{moz}/mozilla-central'
    ret: 0

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  0 draft
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 6
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1 from partition 2 offset 7
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/mozilla-central for phases[77538e1ce4bec5f7aac58a7ceca2da0e38e90a72]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/mozilla-central phases 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 1 0
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]
  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  0 public

Simulate a consumer that is behind
We wait until both the changegroup and pushkey are on the server before
processing on the mirror.

  $ echo laggy-mirror-1 > foo
  $ hg commit -m 'laggy mirror 1'
  $ hg phase --public -r .
  $ echo laggy-mirror-2 > foo
  $ hg commit -m 'laggy mirror 2'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/7dea706c17247788835d1987dc7103ffc365c338
  remote:   https://hg.mozilla.org/mozilla-central/rev/fde0c41176556d1ec1bcf85e66706e5e76012508
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - fde0c41176556d1ec1bcf85e66706e5e76012508
    name: hg-changegroup-2
    nodecount: 2
    path: '{moz}/mozilla-central'
    source: serve

Mirror gets phase update when pulling the changegroup, moving it ahead
of the replication log. (this should be harmless since the state is
accurate)

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 8
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 9
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 10
  vcsreplicator.consumer pulling 1 heads (fde0c41176556d1ec1bcf85e66706e5e76012508) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r fde0c41176556d1ec1bcf85e66706e5e76012508 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 2 changesets with 2 changes to 1 files
  vcsreplicator.consumer   > new changesets 7dea706c1724:fde0c4117655 (hg44 !)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  2 draft
  1 public
  0 public

Now simulate a consumer that is multiple pushes behind

  $ echo double-laggy-1 > foo
  $ hg commit -m 'double laggy 1'
  $ hg phase --public -r .
  $ hg -q push
  $ echo double-laggy-2 > foo
  $ hg commit -m 'double laggy 2'
  $ hg phase --public -r .
  $ hg -q push

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 58017affcc6559ab3237457a5fb1e0e3bde306b1
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 601c8c0d17b02057475d528f022cf5d85da89825
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

Pulling first changegroup will find its phase

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 11
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 12
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 13
  vcsreplicator.consumer pulling 1 heads (58017affcc6559ab3237457a5fb1e0e3bde306b1) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 58017affcc6559ab3237457a5fb1e0e3bde306b1 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 58017affcc65 (hg44 !)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  3 public
  2 public
  1 public
  0 public

Similar behavior for second changegroup

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 14
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 15
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 16
  vcsreplicator.consumer pulling 1 heads (601c8c0d17b02057475d528f022cf5d85da89825) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 601c8c0d17b02057475d528f022cf5d85da89825 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 601c8c0d17b0 (hg44 !)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  4 public
  3 public
  2 public
  1 public
  0 public

Cleanup

  $ hgmo clean
