#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create the repository and push a change

  $ hgmo exec hgssh /create-repo mozilla-central scm_level_1 --non-publishing
  (recorded repository creation in replication log)
  marking repo as non-publishing
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log
  $ standarduser
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central (glob)
  $ consumer --onetime
  * vcsreplicator.consumer writing hgrc: $TESTTMP/repos/mozilla-central/.hg/hgrc (glob)

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial

  $ hg log -T '{rev} {phase}\n'
  0 draft

  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ hg log -T '{rev} {phase}\n'
  0 draft

There should be no pushkey on a push with a draft changeset

  $ consumer --dump --partition 2
  - name: heartbeat-1
  - name: heartbeat-1
  - heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-1
    nodes:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central (glob)

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  0 draft

Locally bumping changeset to public will trigger a pushkey

  $ hg phase --public -r .
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  no changes found
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: recorded updates to phases in replication log in \d\.\d+s (re)
  [1]

  $ consumer --dump --partition 2
  - name: heartbeat-1
  - name: heartbeat-1
  - key: 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-pushkey-1
    namespace: phases
    new: '0'
    old: '1'
    path: '{moz}/mozilla-central'
    ret: 1

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  0 draft
  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
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
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/7dea706c1724
  remote:   https://hg.mozilla.org/mozilla-central/rev/fde0c4117655
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ consumer --dump --partition 2
  - name: heartbeat-1
  - name: heartbeat-1
  - heads:
    - fde0c41176556d1ec1bcf85e66706e5e76012508
    name: hg-changegroup-1
    nodes:
    - 7dea706c17247788835d1987dc7103ffc365c338
    - fde0c41176556d1ec1bcf85e66706e5e76012508
    path: '{moz}/mozilla-central'
    source: serve

Mirror gets phase update when pulling the changegroup, moving it ahead
of the replication log. (this should be harmless since the state is
accurate)

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (fde0c41176556d1ec1bcf85e66706e5e76012508) and 2 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/mozilla-central (glob)

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
  - name: heartbeat-1
  - name: heartbeat-1
  - heads:
    - 58017affcc6559ab3237457a5fb1e0e3bde306b1
    name: hg-changegroup-1
    nodes:
    - 58017affcc6559ab3237457a5fb1e0e3bde306b1
    path: '{moz}/mozilla-central'
    source: serve
  - name: heartbeat-1
  - name: heartbeat-1
  - heads:
    - 601c8c0d17b02057475d528f022cf5d85da89825
    name: hg-changegroup-1
    nodes:
    - 601c8c0d17b02057475d528f022cf5d85da89825
    path: '{moz}/mozilla-central'
    source: serve

Pulling first changegroup will find its phase

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (58017affcc6559ab3237457a5fb1e0e3bde306b1) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central (glob)

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  3 public
  2 public
  1 public
  0 public

Similar behavior for second changegroup

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (601c8c0d17b02057475d528f022cf5d85da89825) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central (glob)

  $ hg -R $TESTTMP/repos/mozilla-central log -T '{rev} {phase}\n'
  4 public
  3 public
  2 public
  1 public
  0 public

Cleanup

  $ hgmo stop
