#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

Create the repository and push a change

  $ hgmo create-repo mozilla-central 1
  (recorded repository creation in replication log)
  $ consumer --onetime
  $ consumer --onetime
  WARNING:vcsreplicator.consumer:created Mercurial repository: $TESTTMP/repos/mozilla-central

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
  remote: legacy replication of phases disabled because vcsreplicator is loaded
  remote: legacy replication of changegroup disabled because vcsreplicator is loaded
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Phases should be updated on normal push

  $ consumer --dump
  - name: heartbeat-1
  - name: heartbeat-1
  - heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-1
    nodes:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  WARNING:vcsreplicator.consumer:pulling 1 heads from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  WARNING:vcsreplicator.consumer:pulled 1 changesets into $TESTTMP/repos/mozilla-central

Creating a bookmark will write a pushkey message

  $ hg bookmark my-bookmark
  $ hg push -B my-bookmark
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  no changes found
  remote: legacy replication of bookmarks disabled because vcsreplicator is loaded
  remote: recorded updates to bookmarks in replication log in \d\.\d+s (re)
  exporting bookmark my-bookmark
  [1]

  $ consumer --dump
  - name: heartbeat-1
  - name: heartbeat-1
  - key: my-bookmark
    name: hg-pushkey-1
    namespace: bookmarks
    new: 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    old: ''
    path: '{moz}/mozilla-central'
    ret: true

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
  no bookmarks set

Consuming the pushkey message will create a bookmark

  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               0:77538e1ce4be

Cleanup

  $ hgmo stop
