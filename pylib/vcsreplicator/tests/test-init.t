#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo exec hgweb0 ls /repo/hg/mozilla

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central debugrequirements
  dotencode
  fncache
  generaldelta
  revlog-compression-zstd
  revlogv1
  share-safe
  sparserevlog
  store

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central

  $ hgmo exec hgweb0 tail -n 5 /var/log/vcsreplicator/consumer.log
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central

  $ hgmo exec hgweb0 ls /repo/hg/mozilla
  mozilla-central

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central debugrequirements
  dotencode
  fncache
  generaldelta
  revlog-compression-zstd
  revlogv1
  share-safe
  sparserevlog
  store

Cleanup

  $ hgmo clean
