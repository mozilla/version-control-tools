#require hgmodocker vcsreplicator

Create a repo and push it to the server

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

Trigger an abandoned transaction on the hgssh (producer) server by creating
a journal file. The next push opening a transaction would normally abort with
"abandoned transaction found".

  $ hgmo exec hgssh touch /repo/hg/mozilla/mozilla-central/.hg/store/journal

The next push recovers the abandoned transaction automatically and succeeds.

  $ touch bar
  $ hg -q commit -A -m second
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: abandoned transaction found; running recover
  remote: rolling back interrupted transaction
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/* (glob)
  remote: recorded changegroup in replication log in \d\.\d+s (re)

The changeset landed on the producer and the journal is gone.

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central log -T '{rev}:{node|short}\n'
  1:* (glob)
  0:* (glob)

  $ hgmo exec hgssh ls /repo/hg/mozilla/mozilla-central/.hg/store/journal
  ls: cannot access '/repo/hg/mozilla/mozilla-central/.hg/store/journal': No such file or directory
  [2]

Replication to the mirrors proceeds as normal.

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central log -T '{rev}:{node|short}\n'
  1:* (glob)
  0:* (glob)

Cleanup

  $ hgmo clean
