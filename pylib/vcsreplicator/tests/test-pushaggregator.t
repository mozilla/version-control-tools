#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create a repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

The aggregate pending topic should contain a heartbeat and repo creation message

  $ papendingconsumer --wait-for-n 2
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  $ papendingconsumer --dump
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'

The aggregate topic should contain a heartbeat and repo creation message

  $ paconsumer --wait-for-n 2
  got a heartbeat-1 message
  got a hg-repo-init-2 message

  $ paconsumer --dump
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

  $ touch foo
  $ hg -q commit -A -m initial
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

The aggregate pending topic should contain a changegroup message

  $ papendingconsumer --start-from 2 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ papendingconsumer --dump --start-from 2
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    last_push_id: 1
    name: hg-heads-1
    path: '{moz}/mozilla-central'

The aggregate topic should contain a changegroup message

  $ paconsumer --start-from 2 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ paconsumer --dump --start-from 2
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    last_push_id: 1
    name: hg-heads-1
    path: '{moz}/mozilla-central'

Stopping the replication on an active mirror should result in no message copy

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop vcsreplicator:2
  vcsreplicator:2: stopped

  $ echo lag > foo
  $ hg commit -m 'push with mirror stopped'
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/8f2fa335d20b56ae20f663553e7e94e4ccdda8ed
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ papendingconsumer --dump --start-from 7
  []

  $ paconsumer --dump --start-from 7
  []

Starting the replication consumer should result in the message being written

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start vcsreplicator:2
  vcsreplicator:2: started

  $ papendingconsumer --start-from 7 --wait-for-n 3
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ papendingconsumer --dump --start-from 7
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    heads:
    - 8f2fa335d20b56ae20f663553e7e94e4ccdda8ed
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    heads:
    - 8f2fa335d20b56ae20f663553e7e94e4ccdda8ed
    last_push_id: 2
    name: hg-heads-1
    path: '{moz}/mozilla-central'

  $ paconsumer --start-from 7 --wait-for-n 3
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ paconsumer --dump --start-from 7
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    heads:
    - 8f2fa335d20b56ae20f663553e7e94e4ccdda8ed
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    heads:
    - 8f2fa335d20b56ae20f663553e7e94e4ccdda8ed
    last_push_id: 2
    name: hg-heads-1
    path: '{moz}/mozilla-central'

Aggregation of messages from multiple partitions works

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop vcsreplicator:*
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)

  $ hgmo create-repo mc2 scm_level_1
  (recorded repository creation in replication log)
  $ hgmo create-repo try scm_level_1
  (recorded repository creation in replication log)
  $ hgmo create-repo users/foo scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start vcsreplicator:*
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)

  $ papendingconsumer --start-from 10 --wait-for-n 6
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a hg-repo-init-2 message
  got a hg-repo-init-2 message

  $ papendingconsumer --dump --start-from 10
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 2
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mc2'
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 4
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/try'
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 7
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/users/foo'

  $ paconsumer --start-from 10 --wait-for-n 6
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a hg-repo-init-2 message
  got a hg-repo-init-2 message

  $ paconsumer --dump --start-from 10
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mc2'
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/try'
  - _created: \d+\.\d+ (re)
    _original_created: \d+\.\d+ (re)
    _original_partition: 0
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/users/foo'

--max-polls argument exits process after N intervals

  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-aggregator --max-polls 1 /etc/mercurial/pushdataaggregator.ini
  vcsreplicator.aggregator hit max polls threshold; exiting
  vcsreplicator.aggregator executing loop exiting gracefully
  vcsreplicator.aggregator process exiting code 0

Cleanup

  $ hgmo clean
