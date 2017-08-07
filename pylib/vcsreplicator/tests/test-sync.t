#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

`hg replicatesync` will synchronize changes

  $ hgmo exec hgssh /set-hgrc-option mozilla-central hooks foo bar

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/mozilla-central replicatesync
  wrote synchronization message into replication log

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    heads:
    - '0000000000000000000000000000000000000000'
    hgrc: '[hooks]
  
      foo = bar
  
  
      '
    name: hg-repo-sync-1
    path: '{moz}/mozilla-central'
    requirements:
    - dotencode
    - fncache
    - generaldelta
    - revlogv1
    - store

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

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
  vcsreplicator.consumer processing hg-repo-sync-1 from partition 2 offset 1
  vcsreplicator.consumer writing hgrc: /repo/hg/mozilla/mozilla-central/.hg/hgrc
  vcsreplicator.consumer pulling 1 heads into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer   $ /var/hg/venv_replication/bin/hg pull -r 0000000000000000000000000000000000000000 ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > remote: Warning: Permanently added the RSA host key for IP address '*' to the list of known hosts. (glob)
  vcsreplicator.consumer   > no changes found
  vcsreplicator.consumer   > added 0 pushes
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 0 changesets into /repo/hg/mozilla/mozilla-central

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/hgrc
  [hooks]
  foo = bar
  

Cleanup

  $ hgmo clean
