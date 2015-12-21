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

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg sendheartbeat
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

Disabling a single Kafka node should still allow push to go through

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg sendheartbeat
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

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
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg sendheartbeat
  sending heartbeat to partition 0
  abort: error sending heartbeat: UNKNOWN
  [255]

  $ echo 2 > foo
  $ hg commit -m 'disabled 2/3 nodes'
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: replication log not available; all writes disabled
  remote: pretxnopen.vcsreplicator hook failed
  abort: push failed on remote
  [255]

Adding node back in should result in being able to push again

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start kafka
  kafka: started
  $ hgmo exec hgweb1 /usr/bin/supervisorctl start kafka
  kafka: started
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg sendheartbeat
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

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
  remote: pretxnopen.vcsreplicator hook failed
  abort: push failed on remote
  [255]

Starting the cluster after full stop should work as long as there was a
clean shutdown (which there was).

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
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/324ebd5068e8
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Stopping Kafka on hgssh node doesn't break pushes
(hgssh is special because it is listed first in the connection string)

  $ hgmo exec hgssh /usr/bin/supervisorctl stop kafka
  kafka: stopped

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg sendheartbeat
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

  $ echo disabled-hgssh > foo
  $ hg commit -m 'disabled hgssh'
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/145bfa9e3455
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Cleanup

  $ hgmo clean
