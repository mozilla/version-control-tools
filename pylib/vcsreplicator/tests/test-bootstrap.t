#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

First we want to test that running the hgssh bootstrap procedure will have the expected
behaviour

Turn off vcsreplicator on hgweb0

  $ hgmo exec hgweb0 supervisorctl stop vcsreplicator:*
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)
  * stopped (glob)

Create several repos on the remaining replication nodes

  $ hgmo create-repo testrepo scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --start-from 0 --wait-for-n 1 /etc/mercurial/vcsreplicator.ini
  got a hg-repo-init-2 message
  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

Fill the repos with some commits to replicate

  $ hg -q clone ssh://$DOCKER_HOSTNAME:$HGPORT/testrepo
  $ hg -q clone ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central

  $ cd testrepo
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/testrepo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/testrepo/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ cd ../mozilla-central
  $ touch foo
  $ hg -q commit -A -m "initial m-c"
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/7a58fdf00b0fe1fa87fa052d9f78a8f28e1239e0
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Modify hgrc files

  $ hgmo exec hgssh /set-hgrc-option mozilla-central hooks dummy value
  $ hgmo exec hgssh /set-hgrc-option testrepo web description random

Run hgssh bootstrap procedure and confirm the format of the returned data
We send the output to a file for use in the hgweb bootstrap procedure

  $ hgmo exec hgssh sudo -u hg -g hg /var/hg/venv_tools/bin/vcsreplicator-bootstrap-hgssh /etc/mercurial/hgrc /var/hg/venv_pash/bin/hg 5 > $TESTTMP/hgssh.json
  $ cat $TESTTMP/hgssh.json | python -m json.tool
  {
      "offsets": {
          "0": [
              2,
              2
          ],
          "1": [
              0,
              0
          ],
          "2": [
              8,
              10
          ],
          "3": [
              0,
              0
          ],
          "4": [
              0,
              0
          ],
          "5": [
              0,
              0
          ],
          "6": [
              0,
              0
          ],
          "7": [
              0,
              0
          ]
      },
      "repositories": [
          "{moz}/mozilla-central",
          "{moz}/testrepo"
      ]
  }

Confirm offsets returned by the bootstrap procedure match offsets from a dump

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         2            2          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        10           10          0 (glob)
  pushdata  *            3         0            0          0 (glob)
  pushdata  *            4         0            0          0 (glob)
  pushdata  *            5         0            0          0 (glob)
  pushdata  *            6         0            0          0 (glob)
  pushdata  *            7         0            0          0 (glob)

Now that we have confirmed the hgssh bootstrap process was successful, we also want to test
that messages received during this process are handled correctly. To do so we
publish some extra commits and add them to the range of bootstrap messages.

  $ echo "test data" > bar
  $ hg add bar
  $ hg -q commit -m "test extra messages commit"
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/89e594ce6b790e64021edfe272c70db75e7304ab
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         2            2          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        13           13          0 (glob)
  pushdata  *            3         0            0          0 (glob)
  pushdata  *            4         0            0          0 (glob)
  pushdata  *            5         0            0          0 (glob)
  pushdata  *            6         0            0          0 (glob)
  pushdata  *            7         0            0          0 (glob)

Edit the JSON object to include the new messages
  >>> import json, os
  >>> tmpdir = os.environ['TESTTMP']
  >>> with open(tmpdir + '/hgssh.json', 'r') as f:
  ...     d = json.loads(f.read())
  >>> d['offsets']['2'] = (8, 13)  # change (8, 10) -> (8, 13)
  >>> with open(tmpdir + '/hgssh_edited.json', 'w') as f:
  ...     f.write(json.dumps(d))

A side effect of the bootstrap process is that re-activating the vcsreplicator
systemd units (or in the tests, supervisord) should start them at a safe location
to begin replicating. Add a commit outside the replication range that should be replicated
once the vcsreplicator daemons restart.

  $ echo "Some changes" > foo
  $ hg -q commit -A -m "Another commit"
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/ba17b5c8e955a5e7f57c478cdd75bc999c5460a1
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Perform bootstrap procedure on hgweb. vcsreplicator is still off on this host so any replication
will be an indication of a successful bootstrap

  $ docker cp $TESTTMP/hgssh_edited.json $HGWEB_0_CID:/etc/mercurial/hgssh.json
  $ hgmo exec hgweb0 sudo -u hg -g hg /var/hg/venv_replication/bin/vcsreplicator-bootstrap-hgweb /etc/mercurial/vcsreplicator.ini /var/hg/venv_replication/bin/hg /etc/mercurial/hgssh.json 1
  vcsreplicator.bootstrap Kafka consumer assigned to replication topic
  vcsreplicator.bootstrap partition 0 of topic pushdata moved to offset 2
  vcsreplicator.bootstrap partition 1 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap partition 2 of topic pushdata moved to offset 8
  vcsreplicator.bootstrap partition 3 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap partition 4 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap partition 5 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap partition 6 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap partition 7 of topic pushdata moved to offset 0
  vcsreplicator.bootstrap finished retrieving messages on partition 2
  vcsreplicator.bootstrap finished retrieving messages from Kafka
  vcsreplicator.bootstrap scheduled clone for {moz}/* (glob)
  vcsreplicator.bootstrap scheduled clone for {moz}/* (glob)
  vcsreplicator.bootstrap extra messages found for {moz}/mozilla-central: 1 total
  vcsreplicator.bootstrap {moz}/* successfully cloned (glob)
  vcsreplicator.bootstrap 1 repositories remaining
  vcsreplicator.bootstrap scheduling extra processing for {moz}/mozilla-central (?)
  vcsreplicator.bootstrap {moz}/* successfully cloned (glob)
  vcsreplicator.bootstrap 0 repositories remaining
  vcsreplicator.bootstrap scheduling extra processing for {moz}/mozilla-central (?)
  vcsreplicator.bootstrap extra processing for {moz}/mozilla-central completed successfully
  vcsreplicator.bootstrap 0 batches remaining
  * bootstrap process complete (glob)



Confirm commits replicated to hgweb host

  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/mozilla-central log
  changeset:   1:89e594ce6b79
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     test extra messages commit
  
  changeset:   0:7a58fdf00b0f
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial m-c
  

  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/testrepo log
  changeset:   0:77538e1ce4be
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial
  
Confirm hgrc replicated to hgweb host

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/hgrc
  [hooks]
  dummy = value
  
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/testrepo/.hg/hgrc
  [web]
  description = random
  

Confirm anticipated offsets on hgweb0

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         2            2    * (glob)
  pushdata  *            1         0            0    * (glob)
  pushdata  *            2        13           16    * (glob)
  pushdata  *            3         0            0    * (glob)
  pushdata  *            4         0            0    * (glob)
  pushdata  *            5         0            0    * (glob)
  pushdata  *            6         0            0    * (glob)
  pushdata  *            7         0            0    * (glob)

Start up vcsreplicator and check that new commits are safely replayed.
We only start partition 2, as the other partitions do not have relevant
messages to play back and their output makes the test non-deterministic


  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:2
  vcsreplicator:2: started

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central log -r tip
  changeset:   2:ba17b5c8e955
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Another commit
  
Verify consumer log output. The indicated initial offsets should start at 13, not 0.

  $ hgmo exec hgweb0 tail -n 17 /var/log/vcsreplicator/consumer.log
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[2] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 13
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 14
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 15
  vcsreplicator.consumer pulling 1 heads (ba17b5c8e955a5e7f57c478cdd75bc999c5460a1) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer   $ /var/hg/venv_replication/bin/hg pull -r ba17b5c8e955a5e7f57c478cdd75bc999c5460a1 ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > added 1 pushes
  vcsreplicator.consumer   > new changesets ba17b5c8e955
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central

Clean

  $ hgmo clean
