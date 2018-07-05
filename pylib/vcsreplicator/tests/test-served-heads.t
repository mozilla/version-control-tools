#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create the repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

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

Wait for heads processor to process all messages.
There are races here. We wait for 6 messages to show up in the pending topic. Then
wait for the consumer to have no lag.

  $ papendingconsumer --wait-for-n 6
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-headsconsumer --wait-for-no-lag /etc/mercurial/vcsreplicator-pending.ini

  $ hgmo exec hgweb0 tail -n 9 /var/log/vcsreplicator/consumer-heads.log
  vcsreplicator.consumer starting consumer for topic=replicatedpushdatapending group=* partitions=all (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 0 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 2
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 3
  vcsreplicator.consumer processing hg-changegroup-2 from partition 0 offset 4
  vcsreplicator.consumer processing hg-heads-1 from partition 0 offset 5
  vcsreplicator.consumer updating replicated heads for /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer /repo/hg/mozilla/mozilla-central/.hg/replicated-data wrote with 1 heads successfully

A file should have been written out in the repo containing the binary heads

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/replicated-data
  \xa2Eheads\x81TwS\x8e\x1c\xe4\xbe\xc5\xf7\xaa\xc5\x8a|\xec\xa2\xda\x0e8\xe9 (esc)
  rLlast_push_id\x01 (no-eol) (esc)

Pushing multiple heads results in appropriate behavior

  $ echo 1 > foo
  $ hg commit -m 1
  $ echo 2 > foo
  $ hg commit -m 2
  $ echo 3 > foo
  $ hg commit -m 3

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

  $ hg log -G -T '{rev} {node} {desc}'
  @  7 4b11352745a6b3eb429ca8cd486dfdc221a4bc62 h2_c2
  |
  o  6 a7e1131c1b7cda934c8eef30932718654c7b4671 h2_c1
  |
  | o  5 4c9443886fe84db9a4a5f29a5777517d2890d308 h1_c2
  | |
  | o  4 5d9ed3f8efffe0777be762f2a35927cc3be3eeef h1_c1
  |/
  o  3 4f52aeca631dfa94331d93cfeaf069526926385a 3
  |
  o  2 e79f1fe30cb27c83477cbb2880367ca8ed54367e 2
  |
  o  1 e325efa1b1fb7cb9e7f231851436db4de63e0a26 1
  |
  o  0 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 initial
  

  $ hg push -f
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 7 changesets with 7 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/e325efa1b1fb7cb9e7f231851436db4de63e0a26
  remote:   https://hg.mozilla.org/mozilla-central/rev/e79f1fe30cb27c83477cbb2880367ca8ed54367e
  remote:   https://hg.mozilla.org/mozilla-central/rev/4f52aeca631dfa94331d93cfeaf069526926385a
  remote:   https://hg.mozilla.org/mozilla-central/rev/5d9ed3f8efffe0777be762f2a35927cc3be3eeef
  remote:   https://hg.mozilla.org/mozilla-central/rev/4c9443886fe84db9a4a5f29a5777517d2890d308
  remote:   https://hg.mozilla.org/mozilla-central/rev/a7e1131c1b7cda934c8eef30932718654c7b4671
  remote:   https://hg.mozilla.org/mozilla-central/rev/4b11352745a6b3eb429ca8cd486dfdc221a4bc62
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Wait for it to be processed by the heads consumer daemon

  $ papendingconsumer --start-from 6 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-headsconsumer --wait-for-no-lag /etc/mercurial/vcsreplicator-pending.ini

  $ hgmo exec hgweb0 tail -n 6 /var/log/vcsreplicator/consumer-heads.log
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 6
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 7
  vcsreplicator.consumer processing hg-changegroup-2 from partition 0 offset 8
  vcsreplicator.consumer processing hg-heads-1 from partition 0 offset 9
  vcsreplicator.consumer updating replicated heads for /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer /repo/hg/mozilla/mozilla-central/.hg/replicated-data wrote with 2 heads successfully

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/replicated-data
  \xa2Eheads\x82TK\x115'E\xa6\xb3\xebB\x9c\xa8\xcdHm\xfd\xc2!\xa4\xbcbTL\x94C\x88o\xe8M\xb9\xa4\xa5\xf2\x9aWwQ}(\x90\xd3\x08Llast_push_id\x02 (no-eol) (esc)

Shutting off a consumer should prevent heads from being aggregated and written out

  $ hgmo exec hgweb1 supervisorctl stop vcsreplicator:*
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)

  $ echo h2_c3 > foo
  $ hg commit -m h2_c3
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/36638cc83b4d9084a2a38f41f345da73390ad05b
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

The new changeset is available in local storage on the mirror

  $ hgmo exec hgweb0 /var/hg/venv_hgweb/bin/hg log -R /repo/hg/mozilla/mozilla-central -r tip
  changeset:   8:36638cc83b4d
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     h2_c3
  

But it isn't available on hgweb because the updates heads aren't written out

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-rev/36638cc83b4d9084a2a38f41f345da73390ad05b
  404
  
  "revision not found: 36638cc83b4d9084a2a38f41f345da73390ad05b"

And the pushlog doesn't expose it
TODO not yet implemented

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes?version=2 --body-file body > /dev/null
  $ python -m json.tool < body
  {
      "lastpushid": 3,
      "pushes": {
          "1": {
              "changesets": [
                  "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "2": {
              "changesets": [
                  "e325efa1b1fb7cb9e7f231851436db4de63e0a26",
                  "e79f1fe30cb27c83477cbb2880367ca8ed54367e",
                  "4f52aeca631dfa94331d93cfeaf069526926385a",
                  "5d9ed3f8efffe0777be762f2a35927cc3be3eeef",
                  "4c9443886fe84db9a4a5f29a5777517d2890d308",
                  "a7e1131c1b7cda934c8eef30932718654c7b4671",
                  "4b11352745a6b3eb429ca8cd486dfdc221a4bc62"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "3": {
              "changesets": [],
              "date": \d+, (re)
              "obsoletechangesets": [
                  "36638cc83b4d9084a2a38f41f345da73390ad05b"
              ],
              "user": "user@example.com"
          }
      }
  }

Re-enabling consumer will result in heads replication and changeset being visible

  $ hgmo exec hgweb1 supervisorctl start vcsreplicator:*
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)

  $ papendingconsumer --start-from 10 --wait-for-n 4
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-heads-1 message

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-headsconsumer --wait-for-no-lag /etc/mercurial/vcsreplicator-pending.ini

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-rev/36638cc83b4d9084a2a38f41f345da73390ad05b
  200
  
  {
  "node": "36638cc83b4d9084a2a38f41f345da73390ad05b",
  "date": [0.0, 0],
  "desc": "h2_c3",
  "backedoutby": "",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "Test User \u003csomeone@example.com\u003e",
  "parents": ["4b11352745a6b3eb429ca8cd486dfdc221a4bc62"],
  "phase": "public",
  "pushid": 3,
  "pushdate": [*, 0], (glob)
  "pushuser": "user@example.com",
  "landingsystem": null
  }

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes?version=2 --body-file body > /dev/null
  $ python -m json.tool < body
  {
      "lastpushid": 3,
      "pushes": {
          "1": {
              "changesets": [
                  "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "2": {
              "changesets": [
                  "e325efa1b1fb7cb9e7f231851436db4de63e0a26",
                  "e79f1fe30cb27c83477cbb2880367ca8ed54367e",
                  "4f52aeca631dfa94331d93cfeaf069526926385a",
                  "5d9ed3f8efffe0777be762f2a35927cc3be3eeef",
                  "4c9443886fe84db9a4a5f29a5777517d2890d308",
                  "a7e1131c1b7cda934c8eef30932718654c7b4671",
                  "4b11352745a6b3eb429ca8cd486dfdc221a4bc62"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "3": {
              "changesets": [
                  "36638cc83b4d9084a2a38f41f345da73390ad05b"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          }
      }
  }

Cleanup

  $ hgmo clean
