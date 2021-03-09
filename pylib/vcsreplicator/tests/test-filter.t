#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create a few repos

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ hgmo create-repo mozilla-unified scm_level_1
  (recorded repository creation in replication log)
  $ hgmo create-repo users/cosheehan_mozilla.com/vct scm_level_1
  (recorded repository creation in replication log)
  $ hgmo create-repo projects/ash scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

Dump state to confirm N replication messages were received

  $ filteredconsumer --dump
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-unified'
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/projects/ash'
  - _created: * (glob)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/mozilla-central'
  - _created: * (glob)
    generaldelta: true
    name: hg-repo-init-2
    path: '{moz}/users/cosheehan_mozilla.com/vct'

Use "onetime" consumer N times for mirror-like host

  $ filteredconsumer --start-from 0 --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 1
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-unified) from partition 0 offset 2
  vcsreplicator.consumer repo {moz}/mozilla-unified filtered by rule unified
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 3
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 4
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/projects/ash) from partition 0 offset 5
  vcsreplicator.consumer created Mercurial repository: {moz}/projects/ash
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: {moz}/mozilla-central
  $ filteredconsumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/users/cosheehan_mozilla.com/vct) from partition 5 offset 0
  vcsreplicator.consumer repo {moz}/users/cosheehan_mozilla.com/vct filtered by rule users

Use "onetime" consumer N times for non-mirror-like host

  $ filteredconsumerdefault --start-from 0 --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 1
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-unified) from partition 0 offset 2
  vcsreplicator.consumer created Mercurial repository: {moz}/mozilla-unified
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 3
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 4
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/projects/ash) from partition 0 offset 5
  vcsreplicator.consumer repo {moz}/projects/ash filtered by rule ash
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer repository already exists: {moz}/mozilla-central
  $ filteredconsumerdefault --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/users/cosheehan_mozilla.com/vct) from partition 5 offset 0
  vcsreplicator.consumer created Mercurial repository: {moz}/users/cosheehan_mozilla.com/vct

Clean

  $ hgmo clean
