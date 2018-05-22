#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

Create the repository and push a change

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central

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
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Phases should be updated on normal push

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

Creating a bookmark will write a pushkey message

  $ hg bookmark my-bookmark
  $ hg push -B my-bookmark
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  no changes found
  remote: recorded updates to bookmarks in replication log in \d\.\d+s (re)
  exporting bookmark my-bookmark
  [1]

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    key: my-bookmark
    name: hg-pushkey-1
    namespace: bookmarks
    new: 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
    old: ''
    path: '{moz}/mozilla-central'
    ret: 1

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
  no bookmarks set

Consuming the pushkey message will create a bookmark

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 4
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1 from partition 2 offset 6
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/mozilla-central for bookmarks[my-bookmark]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/mozilla-central bookmarks my-bookmark '' 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               0:77538e1ce4be

Simulate a client that is behind processing
We send a changegroup and a pushkey but don't process them immediately

  $ echo laggy-mirror > foo
  $ hg commit -m 'simulate laggy mirror'
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
  remote:   https://hg.mozilla.org/mozilla-central/rev/2777163b593873bfa63c7129e02a21becc299ff0
  remote: recorded changegroup in replication log in \d\.\d+s (re)
  updating bookmark my-bookmark

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 2777163b593873bfa63c7129e02a21becc299ff0
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

Mirror gets bookmark updates when pulling the changegroup.

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 7
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 8
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 9
  vcsreplicator.consumer pulling 1 heads (2777163b593873bfa63c7129e02a21becc299ff0) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 2777163b593873bfa63c7129e02a21becc299ff0 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > devel-warn: 'del bookmarks[name]' is deprecated, use 'bookmarks.applychanges'
  vcsreplicator.consumer   > (compatibility will be dropped after Mercurial-4.3, update your code.) at: */pylib/vcsreplicator/vcsreplicator/consumerext.py:* (bookmarks_updatefromremote) (glob)
  vcsreplicator.consumer   > adding remote bookmark my-bookmark
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               1:2777163b5938

Now try something more advanced. Let's do 2 pushes to the server and
see what happens when the mirror pulls a non-tip that no longer has a
bookmark attached.

  $ echo double-laggy-1 > foo
  $ hg commit -m 'double laggy 1'
  $ hg -q push
  $ echo double-laggy-2 > foo
  $ hg commit -m 'double laggy 2'
  $ hg -q push

We should have 2 changegroup messages

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - 031adcaa8ee7e23dd05ce5900645e771a3637682
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - e20ecd72ffa991598a1b26333788345377318231
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

If the mirror pulls, it will see the bookmark attached to a changeset
it doesn't know about since it hasn't pulled it yet. It shouldn't touch
the bookmark.

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 10
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 11

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               1:2777163b5938

  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 12
  vcsreplicator.consumer pulling 1 heads (031adcaa8ee7e23dd05ce5900645e771a3637682) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r 031adcaa8ee7e23dd05ce5900645e771a3637682 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > devel-warn: 'del bookmarks[name]' is deprecated, use 'bookmarks.applychanges'
  vcsreplicator.consumer   > (compatibility will be dropped after Mercurial-4.3, update your code.) at: */pylib/vcsreplicator/vcsreplicator/consumerext.py:* (bookmarks_updatefromremote) (glob)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               1:2777163b5938

But processing the next changegroup message should advance the bookmark by 1

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 13
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 14
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 15
  vcsreplicator.consumer pulling 1 heads (e20ecd72ffa991598a1b26333788345377318231) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r e20ecd72ffa991598a1b26333788345377318231 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > devel-warn: 'del bookmarks[name]' is deprecated, use 'bookmarks.applychanges'
  vcsreplicator.consumer   > (compatibility will be dropped after Mercurial-4.3, update your code.) at: */pylib/vcsreplicator/vcsreplicator/consumerext.py:* (bookmarks_updatefromremote) (glob)
  vcsreplicator.consumer   > adding remote bookmark my-bookmark
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     my-bookmark               3:e20ecd72ffa9

Now test bookmark divergence

  $ hg bookmark divergent
  $ hg push -B divergent
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  no changes found
  remote: recorded updates to bookmarks in replication log in \d+\.\d+s (re)
  exporting bookmark divergent
  [1]

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    key: divergent
    name: hg-pushkey-1
    namespace: bookmarks
    new: e20ecd72ffa991598a1b26333788345377318231
    old: ''
    path: '{moz}/mozilla-central'
    ret: 1

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 16
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 17
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1 from partition 2 offset 18
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/mozilla-central for bookmarks[divergent]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/mozilla-central bookmarks divergent '' e20ecd72ffa991598a1b26333788345377318231
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]

  $ hg -q up 0
  $ echo diverge > foo
  $ hg commit -m 'create divergent head'
  created new head
  $ hg bookmark -f divergent
  $ hg push -f -B divergent
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/e84fdf206e79496713b3a56eae2e16c490475cc8
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  updating bookmark divergent

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    name: heartbeat-1
  - _created: \d+\.\d+ (re)
    heads:
    - e84fdf206e79496713b3a56eae2e16c490475cc8
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 19
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 20
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 21
  vcsreplicator.consumer pulling 1 heads (e84fdf206e79496713b3a56eae2e16c490475cc8) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r e84fdf206e79496713b3a56eae2e16c490475cc8 ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files (+1 heads)
  vcsreplicator.consumer   > devel-warn: 'del bookmarks[name]' is deprecated, use 'bookmarks.applychanges'
  vcsreplicator.consumer   > (compatibility will be dropped after Mercurial-4.3, update your code.) at: */pylib/vcsreplicator/vcsreplicator/consumerext.py:* (bookmarks_updatefromremote) (glob)
  vcsreplicator.consumer   > devel-warn: 'del bookmarks[name]' is deprecated, use 'bookmarks.applychanges'
  vcsreplicator.consumer   > (compatibility will be dropped after Mercurial-4.3, update your code.) at: */pylib/vcsreplicator/vcsreplicator/consumerext.py:* (bookmarks_updatefromremote) (glob)
  vcsreplicator.consumer   > adding remote bookmark divergent
  vcsreplicator.consumer   > adding remote bookmark my-bookmark
  vcsreplicator.consumer   > (run 'hg heads' to see heads, 'hg merge' to merge)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     divergent                 4:e84fdf206e79
     my-bookmark               3:e20ecd72ffa9

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central bookmarks
     divergent                 4:e84fdf206e79
     my-bookmark               3:e20ecd72ffa9

Cleanup

  $ hgmo clean
