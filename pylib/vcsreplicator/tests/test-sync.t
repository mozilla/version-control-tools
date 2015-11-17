#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

`hg replicatesync` will synchronize changes

  $ hgmo exec hgssh /activate-hook mozilla-central foo bar

  $ hgmo exec hgssh /repo/hg/venv_tools/bin/hg -R /repo/hg/mozilla/mozilla-central replicatesync
  wrote synchronization message into replication log

  $ consumer --dump --partition 2
  - name: hg-repo-init-1
    path: '{moz}/mozilla-central'
  - heads:
    - '0000000000000000000000000000000000000000'
    hgrc: '[hooks]
  
      foo = bar
  
  
      '
    name: hg-repo-sync-1
    path: '{moz}/mozilla-central'
    requirements:
    - dotencode
    - fncache
    - revlogv1
    - store

Race condition between applying messages and printing log
  $ sleep 2

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
  * vcsreplicator.consumer writing hgrc: /repo/hg/mozilla/mozilla-central/.hg/hgrc (glob)
  * vcsreplicator.consumer pulling 1 heads into /repo/hg/mozilla/mozilla-central (glob)
  * vcsreplicator.consumer pulled 0 changesets into /repo/hg/mozilla/mozilla-central (glob)

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/hgrc
  [hooks]
  foo = bar
  

Cleanup

  $ hgmo stop
