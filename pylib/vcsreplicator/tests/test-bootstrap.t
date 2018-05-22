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


Clean

  $ hgmo clean
