#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

Disabling a single Kafka node should still allow push to go through

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ echo 1 > foo
  $ hg commit -m 'disabled 1/3 nodes'
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/40a8cea9915c
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Disabling 2 Kafka nodes should result in no quorum and failure to push

  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ echo 2 > foo
  $ hg commit -m 'disabled 2/3 nodes'
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: replication log not available; all writes disabled
  abort: pretxnopen.vcsreplicator hook failed
  [255]

Adding node back in should result in being able to push again

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start kafka
  kafka: started
  $ hgmo exec hgweb1 /usr/bin/supervisorctl start kafka
  kafka: started
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/f783dc6187dd
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Fully stopping the cluster shoud result in sane error message

  $ hgmo exec hgssh /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop kafka
  kafka: stopped

  $ echo 3 > foo
  $ hg commit -m 'full stop'
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: replication log not available; all writes disabled
  abort: pretxnopen.vcsreplicator hook failed
  [255]

Starting the cluster after full stop should still error because cluster
is configured to not restart after full state loss without human
intervention

  $ hgmo exec hgssh /usr/bin/supervisorctl start kafka
  kafka: started
  $ hgmo exec hgweb0 /usr/bin/supervisorctl start kafka
  kafka: started
  $ hgmo exec hgweb1 /usr/bin/supervisorctl start kafka
  kafka: started

  $ sleep 3

  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: replication log not available; all writes disabled
  abort: pretxnopen.vcsreplicator hook failed
  [255]

Cleanup

  $ hgmo stop
