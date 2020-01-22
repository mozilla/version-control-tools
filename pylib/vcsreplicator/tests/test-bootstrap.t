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
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo create-repo deleterepo scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo create-repo filterrepo scm_level_1
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

Insert some replication rules on hgweb0
Explicit exclude "filterrepo" for testing, include everything else

  $ hgmo exec hgweb0 /set-config-option /etc/mercurial/vcsreplicator.ini replicationrules exclude.testrule path:{moz}/filterrepo
  $ hgmo exec hgweb0 /set-config-option /etc/mercurial/vcsreplicator.ini replicationrules include.rest re:\{moz\}/.\*


Run hgssh bootstrap procedure and confirm the format of the returned data
We send the output to a file for use in the hgweb bootstrap procedure

  $ hgmo exec hgssh sudo -u hg -g hg /var/hg/venv_tools/bin/vcsreplicator-bootstrap-hgssh /etc/mercurial/hgrc /var/hg/venv_pash/bin/hg --workers 1 --output /home/hg/hgssh.json
  * * vcsreplicator.bootstrap gathered initial Kafka offsets (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/deleterepo (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/filterrepo (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/mozilla-central (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/testrepo (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/deleterepo successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/filterrepo successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/mozilla-central successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/testrepo successfully (glob)
  * * vcsreplicator.bootstrap gathered final Kafka offsets (glob)
  {"repositories": ["{moz}/deleterepo", "{moz}/filterrepo", "{moz}/mozilla-central", "{moz}/testrepo"], "offsets": {"0": [6, 8], "1": [0, 0], "2": [10, 12], "3": [0, 0], "4": [0, 0], "5": [0, 0], "6": [0, 0], "7": [0, 0]}}
  * * vcsreplicator.bootstrap hgssh bootstrap process complete! (glob)
  * * vcsreplicator.bootstrap writing output to /home/hg/hgssh.json (glob)
  $ hgmo exec hgssh sudo -u hg -g hg cat /home/hg/hgssh.json | python -m json.tool
  {
      "offsets": {
          "0": [
              6,
              8
          ],
          "1": [
              0,
              0
          ],
          "2": [
              10,
              12
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
          "{moz}/deleterepo",
          "{moz}/filterrepo",
          "{moz}/mozilla-central",
          "{moz}/testrepo"
      ]
  }
  $ docker cp $SSH_CID:/home/hg/hgssh.json $TESTTMP/hgssh.json

Check the logs on hgssh

  $ hgmo exec hgssh cat /var/log/vcsrbootstrap/bootstrap.log
  * * vcsreplicator.bootstrap gathered initial Kafka offsets (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/deleterepo (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/filterrepo (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/mozilla-central (glob)
  * * vcsreplicator.bootstrap calling `replicatesync --bootstrap` on /repo/hg/mozilla/testrepo (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/deleterepo successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/filterrepo successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/mozilla-central successfully (glob)
  * * vcsreplicator.bootstrap called `replicatesync --bootstrap` on /repo/hg/mozilla/testrepo successfully (glob)
  * * vcsreplicator.bootstrap gathered final Kafka offsets (glob)
  * * vcsreplicator.bootstrap hgssh bootstrap process complete! (glob)
  * * vcsreplicator.bootstrap writing output to /home/hg/hgssh.json (glob)

Confirm offsets returned by the bootstrap procedure match offsets from a dump

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         8            8          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        12           12          0 (glob)
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
  pushdata  *            0         8            8          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        16           16          0 (glob)
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
  >>> d['offsets']['2'] = (10, 16)  # change (10, 12) -> (10, 16)
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

Print offsets on hgweb1 host

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         8            8          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        20           20          0 (glob)
  pushdata  *            3         0            0          0 (glob)
  pushdata  *            4         0            0          0 (glob)
  pushdata  *            5         0            0          0 (glob)
  pushdata  *            6         0            0          0 (glob)
  pushdata  *            7         0            0          0 (glob)

Delete the "deleterepo" to generate an error in the hgweb output

  $ hgmo exec hgssh sudo rm -rf /repo/hg/mozilla/deleterepo

Perform bootstrap procedure on hgweb. vcsreplicator is still off on this host so any replication
will be an indication of a successful bootstrap

  $ docker cp $TESTTMP/hgssh_edited.json $HGWEB_0_CID:/etc/mercurial/hgssh.json
  $ hgmo exec hgweb0 sudo -u hg -g hg /var/hg/venv_replication/bin/vcsreplicator-bootstrap-hgweb /etc/mercurial/vcsreplicator.ini /etc/mercurial/hgssh.json --workers 1
  * * vcsreplicator.bootstrap reading hgssh JSON document (glob)
  * * vcsreplicator.bootstrap JSON document read (glob)
  * * vcsreplicator.bootstrap assigning the consumer to partition 0 (glob)
  * * vcsreplicator.bootstrap seeking the consumer to offset 6 (glob)
  * * vcsreplicator.bootstrap partition 0 of topic pushdata moved to offset 6 (glob)
  * * vcsreplicator.bootstrap message on partition 0, offset 6 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 0, offset 7 has been collected (glob)
  * * vcsreplicator.bootstrap finished retrieving messages on partition 0 (glob)
  * * vcsreplicator.bootstrap assigning the consumer to partition 2 (glob)
  * * vcsreplicator.bootstrap seeking the consumer to offset 10 (glob)
  * * vcsreplicator.bootstrap partition 2 of topic pushdata moved to offset 10 (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 10 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 11 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 12 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 13 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 14 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 15 has been collected (glob)
  * * vcsreplicator.bootstrap finished retrieving messages on partition 2 (glob)
  * * vcsreplicator.bootstrap finished retrieving messages from Kafka (glob)
  * * vcsreplicator.bootstrap processing messages for partition 0 (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap processing messages for partition 2 (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap extra messages found for {moz}/mozilla-central: 1 total (glob)
  * * vcsreplicator.bootstrap extra messages found for {moz}/mozilla-central: 2 total (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap error triggering replication of Mercurial repo {moz}/deleterepo: (255, b'pulling from ssh://hgssh/deleterepo\nremote: Warning: Permanently added the RSA host key for IP address * to the list of known hosts.\nremote: requested repo deleterepo does not exist', b'abort: no suitable response from remote hg!') (glob)
  * * vcsreplicator.bootstrap 2 repositories remaining (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap {moz}/mozilla-central successfully cloned (glob)
  * * vcsreplicator.bootstrap 1 repositories remaining (glob)
  * * vcsreplicator.bootstrap scheduling extra processing for {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap {moz}/testrepo successfully cloned (glob)
  * * vcsreplicator.bootstrap 0 repositories remaining (glob)
  * * vcsreplicator.bootstrap extra processing for {moz}/mozilla-central completed successfully (glob)
  * * vcsreplicator.bootstrap 0 batches remaining (glob)
  * bootstrap process complete (glob)
  [1]


Confirm commits replicated to hgweb host

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central log
  changeset:   1:89e594ce6b79
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     test extra messages commit
  
  changeset:   0:7a58fdf00b0f
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial m-c
  

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/testrepo log
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
  pushdata  *            0         8            8    * (glob)
  pushdata  *            1         0            0    * (glob)
  pushdata  *            2        16           20    * (glob)
  pushdata  *            3         0            0    * (glob)
  pushdata  *            4         0            0    * (glob)
  pushdata  *            5         0            0    * (glob)
  pushdata  *            6         0            0    * (glob)
  pushdata  *            7         0            0    * (glob)

Start up vcsreplicator and check that new commits are safely replayed.
Start partition 2 last to ensure the relevant test output appears at the
bottom of the log file.


  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:0
  vcsreplicator:0: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:1
  vcsreplicator:1: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:3
  vcsreplicator:3: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:4
  vcsreplicator:4: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:5
  vcsreplicator:5: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:6
  vcsreplicator:6: started
  $ hgmo exec hgweb0 supervisorctl start vcsreplicator:7
  vcsreplicator:7: started
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

  $ hgmo exec hgweb0 cat /var/log/vcsrbootstrap/consumer.log
  repository does not exist: /repo/hg/mozilla/deleterepo
  created Mercurial repository: /repo/hg/mozilla/deleterepo
  pulling 1 heads into /repo/hg/mozilla/deleterepo
    $ /var/hg/venv_replication/bin/hg pull -r0000000000000000000000000000000000000000 -- ssh://hgssh/deleterepo
    > pulling from ssh://hgssh/deleterepo
    > remote: Warning: Permanently added the RSA host key for IP address '*' to the list of known hosts. (glob)
    > remote: requested repo deleterepo does not exist
    > abort: no suitable response from remote hg!
    [255]
  repository does not exist: /repo/hg/mozilla/mozilla-central
  created Mercurial repository: /repo/hg/mozilla/mozilla-central
  writing hgrc: /repo/hg/mozilla/mozilla-central/.hg/hgrc
  pulling 1 heads into /repo/hg/mozilla/mozilla-central
    $ /var/hg/venv_replication/bin/hg pull -r7a58fdf00b0fe1fa87fa052d9f78a8f28e1239e0 -- ssh://hgssh/mozilla-central
    > pulling from ssh://hgssh/mozilla-central
    > adding changesets
    > adding manifests
    > adding file changes
    > received pushlog entry for unknown changeset 89e594ce6b790e64021edfe272c70db75e7304ab; ignoring
    > added 1 pushes
    > updating moz-owner file
    > added 1 changesets with 1 changes to 1 files
    > new changesets 7a58fdf00b0f
    > (run 'hg update' to get a working copy)
    [0]
  pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  repository does not exist: /repo/hg/mozilla/testrepo
  created Mercurial repository: /repo/hg/mozilla/testrepo
  writing hgrc: /repo/hg/mozilla/testrepo/.hg/hgrc
  pulling 1 heads into /repo/hg/mozilla/testrepo
    $ /var/hg/venv_replication/bin/hg pull -r77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 -- ssh://hgssh/testrepo
    > pulling from ssh://hgssh/testrepo
    > adding changesets
    > adding manifests
    > adding file changes
    > added 1 pushes
    > updating moz-owner file
    > added 1 changesets with 1 changes to 1 files
    > new changesets 77538e1ce4be
    > (run 'hg update' to get a working copy)
    [0]
  pulled 1 changesets into /repo/hg/mozilla/testrepo
  pulling 1 heads (89e594ce6b790e64021edfe272c70db75e7304ab) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
    $ /var/hg/venv_replication/bin/hg pull -r89e594ce6b790e64021edfe272c70db75e7304ab -- ssh://hgssh/mozilla-central
    > pulling from ssh://hgssh/mozilla-central
    > searching for changes
    > adding changesets
    > adding manifests
    > adding file changes
    > received pushlog entry for unknown changeset ba17b5c8e955a5e7f57c478cdd75bc999c5460a1; ignoring
    > added 1 pushes
    > added 1 changesets with 1 changes to 1 files
    > new changesets 89e594ce6b79
    > (run 'hg update' to get a working copy)
    [0]
  pulled 1 changesets into /repo/hg/mozilla/mozilla-central

Verify bootstrap log is correct

  $ hgmo exec hgweb0 cat /var/log/vcsrbootstrap/bootstrap.log
  * * vcsreplicator.bootstrap reading hgssh JSON document (glob)
  * * vcsreplicator.bootstrap JSON document read (glob)
  * * vcsreplicator.bootstrap assigning the consumer to partition 0 (glob)
  * * vcsreplicator.bootstrap seeking the consumer to offset 6 (glob)
  * * vcsreplicator.bootstrap partition 0 of topic pushdata moved to offset 6 (glob)
  * * vcsreplicator.bootstrap message on partition 0, offset 6 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 0, offset 7 has been collected (glob)
  * * vcsreplicator.bootstrap finished retrieving messages on partition 0 (glob)
  * * vcsreplicator.bootstrap assigning the consumer to partition 2 (glob)
  * * vcsreplicator.bootstrap seeking the consumer to offset 10 (glob)
  * * vcsreplicator.bootstrap partition 2 of topic pushdata moved to offset 10 (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 10 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 11 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 12 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 13 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 14 has been collected (glob)
  * * vcsreplicator.bootstrap message on partition 2, offset 15 has been collected (glob)
  * * vcsreplicator.bootstrap finished retrieving messages on partition 2 (glob)
  * * vcsreplicator.bootstrap finished retrieving messages from Kafka (glob)
  * * vcsreplicator.bootstrap processing messages for partition 0 (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap processing messages for partition 2 (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap scheduled clone for {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap extra messages found for {moz}/mozilla-central: 1 total (glob)
  * * vcsreplicator.bootstrap extra messages found for {moz}/mozilla-central: 2 total (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/deleterepo (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap error triggering replication of Mercurial repo {moz}/deleterepo: (255, b'pulling from ssh://hgssh/deleterepo\nremote: Warning: Permanently added the RSA host key for IP address * to the list of known hosts.\nremote: requested repo deleterepo does not exist', b'abort: no suitable response from remote hg!') (glob)
  * * vcsreplicator.bootstrap 2 repositories remaining (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap syncing repo: {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap {moz}/mozilla-central successfully cloned (glob)
  * * vcsreplicator.bootstrap 1 repositories remaining (glob)
  * * vcsreplicator.bootstrap scheduling extra processing for {moz}/mozilla-central (glob)
  * * vcsreplicator.bootstrap exiting sync for: {moz}/testrepo (glob)
  * * vcsreplicator.bootstrap {moz}/testrepo successfully cloned (glob)
  * * vcsreplicator.bootstrap 0 repositories remaining (glob)
  * * vcsreplicator.bootstrap extra processing for {moz}/mozilla-central completed successfully (glob)
  * * vcsreplicator.bootstrap 0 batches remaining (glob)
  * bootstrap process complete (glob)

Print offsets for vcsreplicator after full bootstrap and vcsreplicator daemons activated.

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *            0         8            8          0 (glob)
  pushdata  *            1         0            0          0 (glob)
  pushdata  *            2        20           20          0 (glob)
  pushdata  *            3         0            0          0 (glob)
  pushdata  *            4         0            0          0 (glob)
  pushdata  *            5         0            0          0 (glob)
  pushdata  *            6         0            0          0 (glob)
  pushdata  *            7         0            0          0 (glob)

Ensure the audit output is in the correct format

  $ hgmo exec hgweb0 cat /repo/hg/hgweb_bootstrap_out.json | python -m json.tool
  {
      "{moz}/deleterepo": [
          "error triggering replication of Mercurial repo {moz}/deleterepo: (255, b'pulling from ssh://hgssh/deleterepo\\nremote: Warning: Permanently added the RSA host key for IP address '*.*.*.*' to the list of known hosts.\\nremote: requested repo deleterepo does not exist', b'abort: no suitable response from remote hg!')" (glob)
      ],
      "{moz}/filterrepo": [
          "filtered by rule testrule"
      ]
  }

Clean

  $ hgmo clean
