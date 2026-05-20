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
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ paconsumer --wait-for-n 6
  got a heartbeat-1 message
  got a hg-repo-init-2: (repo: {moz}/mozilla-central) message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be']) message
  got a hg-heads-1: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be'], last_push_id: 1) message
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
  got a hg-repo-init-2: (repo: {moz}/private/ignore) message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2: (repo: {moz}/private/ignore, heads: ['77538e1ce4be']) message
  got a hg-heads-1: (repo: {moz}/private/ignore, heads: ['77538e1ce4be'], last_push_id: 1) message
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
  got a hg-repo-init-2: (repo: {moz}/integration/foo_Bar-baz) message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2: (repo: {moz}/integration/foo_Bar-baz, heads: ['77538e1ce4be']) message
  got a hg-heads-1: (repo: {moz}/integration/foo_Bar-baz, heads: ['77538e1ce4be'], last_push_id: 1) message
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
  got a hg-repo-init-2: (repo: {moz}/ignored-repo) message

  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped heartbeat-1 message in partition 0 for group pulsenotifier
  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped hg-repo-init-2 message in partition 0 for group pulsenotifier

  $ pulseconsumer --wait-for-no-lag

  $ pulse dump-messages exchange/hgpushes/v2 v2
  []

Simulate a daemon restart mid-stream: the notifier sees hg-heads-1 without the
paired hg-changegroup-2 and falls back to heads-1 data.

Restart the notifier after the skip test above.

  $ hgmo exec hgssh supervisorctl start pulsenotifier
  pulsenotifier: started

  $ cd mozilla-central
  $ touch bar
  $ hg -q commit -A -m 'second commit'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/* (glob)
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Use paconsumer to confirm all 4 messages (including hg-heads-1) are in the topic
before waiting on the daemon. Without this, pulseconsumer --wait-for-no-lag can
return as soon as the changegroup offset is committed (lag=0) while hg-heads-1
is still in-flight from hgssh's async lock-release callback.

  $ paconsumer --start-from 20 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['*']) message (glob)
  got a hg-heads-1: (repo: {moz}/mozilla-central, heads: ['*'], last_push_id: 2) message (glob)
  $ pulseconsumer --wait-for-no-lag

Verify the normal notification was sent before proceeding to the restart scenario.

  $ pulse dump-messages exchange/hgpushes/v2 v2
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: mozilla-central
    data:
      heads:
      - * (glob)
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=1&endID=2
        push_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=1&endID=2
        pushid: 2
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/mozilla-central
      source: serve
    type: changegroup.1

Stop the notifier and do a third push, then simulate a daemon restart between
the hg-changegroup-2 and hg-heads-1 messages. Skipping those three messages leaves
hg-heads-1 for the restarted daemon to process with an empty pending_changegroups
buffer.

  $ hgmo exec hgssh supervisorctl stop pulsenotifier
  pulsenotifier: stopped

  $ touch baz
  $ hg -q commit -A -m 'third commit'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/* (glob)
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Confirm all 4 push-3 messages are in the topic before skipping.

  $ paconsumer --start-from 24 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['*']) message (glob)
  got a hg-heads-1: (repo: {moz}/mozilla-central, heads: ['*'], last_push_id: 3) message (glob)

Skip the pretxnopen heartbeat, the pretxnclose heartbeat, and hg-changegroup-2,
advancing the notifier's committed offset past them without buffering.

  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped heartbeat-1 message in partition \d+ for group pulsenotifier (re)
  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped heartbeat-1 message in partition \d+ for group pulsenotifier (re)
  $ hgmo exec hgssh /var/hg/venv_tools/bin/vcsreplicator-pulse-notifier --skip /etc/mercurial/notifications.ini
  skipped hg-changegroup-2 message in partition \d+ for group pulsenotifier (re)

  $ hgmo exec hgssh supervisorctl start pulsenotifier
  pulsenotifier: started
  $ pulseconsumer --wait-for-no-lag

The notifier should have logged the fallback and still sent a notification.

  $ hgmo exec hgssh grep "falling back" /var/log/pulsenotifier.log
  vcsreplicator.pushnotifications hg-heads-1 with no pending changegroup for {moz}/mozilla-central; falling back to heads-1 data

The third push's changegroup.1 notification is present. source is "serve" (hardcoded
in the fallback path since hg-heads-1 does not carry the original source).
pulse dump-messages consumes from the queue, so only messages since the last
dump are shown here.

  $ pulse dump-messages exchange/hgpushes/v2 v2
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: mozilla-central
    data:
      heads:
      - * (glob)
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&full=1&startID=2&endID=3
        push_json_url: https://hg.mozilla.org/mozilla-central/json-pushes?version=2&startID=2&endID=3
        pushid: 3
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/mozilla-central
      source: serve
    type: changegroup.1

Cleanup

  $ hgmo clean
