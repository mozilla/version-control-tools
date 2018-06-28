#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ pulse create-queue exchange/hgpushes/v1 v1
  $ pulse create-queue exchange/hgpushes/v2 v2

Create a repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

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

  $ paconsumer --wait-for-n 6
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message
  $ pulseconsumer --wait-for-no-lag

  $ pulse dump-messages exchange/hgpushes/v1 v1
  - _meta:
      exchange: exchange/hgpushes/v1
      routing_key: mozilla-central
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    pushlog_pushes:
    - push_full_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=0&endID=1
      push_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=0&endID=1
      pushid: 1
      time: \d+ (re)
      user: user@example.com
    repo_url: https://hg.mozilla.org/mozilla-central

Message written to v2 with message type

  $ pulse dump-messages exchange/hgpushes/v2 v2
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: mozilla-central
    data:
      repo_url: https://hg.mozilla.org/mozilla-central
    type: newrepo.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: mozilla-central
    data:
      heads:
      - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=0&endID=1
        push_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=0&endID=1
        pushid: 1
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/mozilla-central
      source: serve
    type: changegroup.1

Repos under ignore paths are ignored

  $ cd ..
  $ hgmo create-repo private/ignore scm_level_1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/private/ignore
  $ cd ignore
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ paconsumer --start-from 6 --wait-for-n 6
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message
  $ pulseconsumer --wait-for-no-lag

  $ hgmo exec hgssh grep private /var/log/pulsenotifier.log
  vcsreplicator.pushnotifications ignoring repo because path in ignore list: {moz}/private/ignore
  vcsreplicator.pushnotifications ignoring repo because path in ignore list: {moz}/private/ignore
  vcsreplicator.pushnotifications ignoring repo because path in ignore list: {moz}/private/ignore

  $ cd ..

Routing keys with slashes and dashes and underscores work

  $ hgmo create-repo integration/foo_Bar-baz scm_level_1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/integration/foo_Bar-baz
  $ cd foo_Bar-baz
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ paconsumer --start-from 12 --wait-for-n 6
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message
  $ pulseconsumer --wait-for-no-lag

  $ pulse dump-messages exchange/hgpushes/v1 v1
  - _meta:
      exchange: exchange/hgpushes/v1
      routing_key: integration/foo_Bar-baz
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    pushlog_pushes:
    - push_full_json_url: https://hg.mozilla.org/integration/foo_Bar-baz/json-pushes?version=2&full=1&startID=0&endID=1
      push_json_url: https://hg.mozilla.org/integration/foo_Bar-baz/json-pushes?version=2&startID=0&endID=1
      pushid: 1
      time: \d+ (re)
      user: user@example.com
    repo_url: https://hg.mozilla.org/integration/foo_Bar-baz

  $ pulse dump-messages exchange/hgpushes/v2 v2
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: integration/foo_Bar-baz
    data:
      repo_url: https://hg.mozilla.org/integration/foo_Bar-baz
    type: newrepo.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: integration/foo_Bar-baz
    data:
      heads:
      - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/integration/foo_Bar-baz/json-pushes?version=2&full=1&startID=0&endID=1
        push_json_url: https://hg.mozilla.org/integration/foo_Bar-baz/json-pushes?version=2&startID=0&endID=1
        pushid: 1
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/integration/foo_Bar-baz
      source: serve
    type: changegroup.1

  $ cd ..

Pulse client can skip messages

  $ hgmo exec hgssh supervisorctl stop pulsenotifier
  pulsenotifier: stopped

  $ hgmo create-repo ignored-repo scm_level_1
  (recorded repository creation in replication log)

  $ paconsumer --start-from 18 --wait-for-n 2
  got a heartbeat-1 message
  got a hg-repo-init-2 message

  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped heartbeat-1 message in partition 0 for group pulsenotifier
  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped hg-repo-init-2 message in partition 0 for group pulsenotifier

  $ pulseconsumer --wait-for-no-lag

  $ pulse dump-messages exchange/hgpushes/v2 v2
  []

Cleanup

  $ hgmo clean
