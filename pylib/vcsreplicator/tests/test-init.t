#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo exec hgweb0 ls /repo/hg/mozilla

  $ hgmo create-repo mozilla-central scm_level_3 --no-generaldelta
  (recorded repository creation in replication log)

  $ hgmo exec hgssh cat /repo/hg/mozilla/mozilla-central/.hg/requires
  dotencode
  fncache
  revlogv1
  store

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    generaldelta: false
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central

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

  $ hgmo exec hgweb0 ls /repo/hg/mozilla
  mozilla-central

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/requires
  dotencode
  fncache
  revlogv1
  store

generaldelta is preserved

  $ hgmo create-repo mcgd scm_level_3
  (recorded repository creation in replication log)

  $ hgmo exec hgssh cat /repo/hg/mozilla/mcgd/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  store

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mcgd'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 1
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 1
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mcgd

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mcgd/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  store

Cleanup

  $ hgmo clean
