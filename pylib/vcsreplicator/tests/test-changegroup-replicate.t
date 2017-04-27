#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create the repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

Pushing the initial commit will result in replication messages

  $ touch foo
  $ hg -q commit -A -m initial

  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
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

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'
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
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hgmo exec hgweb0 cat /var/log/vcsreplicator/consumer.log
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central

Pushing multiple commits results in sane behavior

  $ echo 1 > foo
  $ hg commit -m 1
  $ echo 2 > foo
  $ hg commit -m 2
  $ echo 3 > foo
  $ hg commit -m 3

  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/e325efa1b1fb7cb9e7f231851436db4de63e0a26
  remote:   https://hg.mozilla.org/mozilla-central/rev/e79f1fe30cb27c83477cbb2880367ca8ed54367e
  remote:   https://hg.mozilla.org/mozilla-central/rev/4f52aeca631dfa94331d93cfeaf069526926385a
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ consumer --dump --partition 2 --start-from 5
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 4f52aeca631dfa94331d93cfeaf069526926385a
    name: hg-changegroup-2
    nodecount: 3
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 4
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 6
  vcsreplicator.consumer pulling 1 heads (4f52aeca631dfa94331d93cfeaf069526926385a) and 3 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer pulled 3 changesets into $TESTTMP/repos/mozilla-central

  $ hg log -R $TESTTMP/repos/mozilla-central -T '{rev}:{node}\n'
  3:4f52aeca631dfa94331d93cfeaf069526926385a
  2:e79f1fe30cb27c83477cbb2880367ca8ed54367e
  1:e325efa1b1fb7cb9e7f231851436db4de63e0a26
  0:77538e1ce4bec5f7aac58a7ceca2da0e38e90a72

  $ hgmo exec hgweb0 cat /var/log/vcsreplicator/consumer.log
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 4
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 6
  vcsreplicator.consumer pulling 1 heads (4f52aeca631dfa94331d93cfeaf069526926385a) and 3 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 3 changesets into /repo/hg/mozilla/mozilla-central

Pushing multiple heads results in appropriate behavior

  $ echo h1_c1 > foo
  $ hg commit -m h1_c1
  $ echo h1_c2 > foo
  $ hg commit -m h1_c2
  $ hg -q up 3
  $ echo h2_c1 > foo
  $ hg commit -m h2_c1
  created new head
  $ echo h2_c2 > foo
  $ hg commit -m h2_c2

  $ hg push -f
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 4 changesets with 4 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/5d9ed3f8efffe0777be762f2a35927cc3be3eeef
  remote:   https://hg.mozilla.org/mozilla-central/rev/4c9443886fe84db9a4a5f29a5777517d2890d308
  remote:   https://hg.mozilla.org/mozilla-central/rev/a7e1131c1b7cda934c8eef30932718654c7b4671
  remote:   https://hg.mozilla.org/mozilla-central/rev/4b11352745a6b3eb429ca8cd486dfdc221a4bc62
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ consumer --dump --partition 2 --start-from 8
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 4c9443886fe84db9a4a5f29a5777517d2890d308
    - 4b11352745a6b3eb429ca8cd486dfdc221a4bc62
    name: hg-changegroup-2
    nodecount: 4
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 7
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 8
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 9
  vcsreplicator.consumer pulling 2 heads (4c9443886fe84db9a4a5f29a5777517d2890d308, 4b11352745a6b3eb429ca8cd486dfdc221a4bc62) and 4 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer pulled 4 changesets into $TESTTMP/repos/mozilla-central

  $ hg log -R $TESTTMP/repos/mozilla-central -T '{rev}:{node}\n'
  7:4b11352745a6b3eb429ca8cd486dfdc221a4bc62
  6:a7e1131c1b7cda934c8eef30932718654c7b4671
  5:4c9443886fe84db9a4a5f29a5777517d2890d308
  4:5d9ed3f8efffe0777be762f2a35927cc3be3eeef
  3:4f52aeca631dfa94331d93cfeaf069526926385a
  2:e79f1fe30cb27c83477cbb2880367ca8ed54367e
  1:e325efa1b1fb7cb9e7f231851436db4de63e0a26
  0:77538e1ce4bec5f7aac58a7ceca2da0e38e90a72

  $ hgmo exec hgweb0 cat /var/log/vcsreplicator/consumer.log
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 4
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 6
  vcsreplicator.consumer pulling 1 heads (4f52aeca631dfa94331d93cfeaf069526926385a) and 3 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 3 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 7
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 8
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 9
  vcsreplicator.consumer pulling 2 heads (4c9443886fe84db9a4a5f29a5777517d2890d308, 4b11352745a6b3eb429ca8cd486dfdc221a4bc62) and 4 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer pulled 4 changesets into /repo/hg/mozilla/mozilla-central

Cleanup

  $ hgmo clean
