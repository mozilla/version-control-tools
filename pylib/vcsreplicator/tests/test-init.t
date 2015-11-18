#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo exec hgweb0 ls /repo/hg/mozilla

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: hg-repo-init-1
    path: '{moz}/mozilla-central'

  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central (glob)

  $ hgmo exec hgweb0 cat /var/log/vcsreplicator/consumer.log
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central (glob)

  $ hgmo exec hgweb0 ls /repo/hg/mozilla
  mozilla-central

Cleanup

  $ hgmo stop
