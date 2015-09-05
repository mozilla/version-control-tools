#require docker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central 1
  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/mozilla-central
  $ cd mozilla-central

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg bookmark bm1
  $ echo bm1 > foo
  $ hg commit -m 'bm1 commit 1'
  $ hg -q up -r 0
  $ hg bookmark bm2
  $ echo bm2 > foo
  $ hg commit -m 'bm2 commit 1'
  created new head

  $ hg log -G
  @  changeset:   2:793dd4558cab
  |  bookmark:    bm2
  |  tag:         tip
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     bm2 commit 1
  |
  | o  changeset:   1:b8c2ad26671f
  |/   bookmark:    bm1
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     bm1 commit 1
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ hg push -B bm1
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in \d+\.\ds (re)
  remote: replication of bookmarks data completed successfully in \d+\.\ds (re)
  remote: replication of changegroup data completed successfully in \d+\.\ds (re)
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/96ee1d7354c4
  remote:   https://hg.mozilla.org/mozilla-central/rev/b8c2ad26671f
  exporting bookmark bm1

  $ hg push -B bm2
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in \d+\.\ds (re)
  remote: replication of bookmarks data completed successfully in \d+\.\ds (re)
  remote: replication of changegroup data completed successfully in \d+\.\ds (re)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/793dd4558cab
  exporting bookmark bm2

Bookmarks get replicated to mirrors

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-bookmarks
  200
  
  {
  "node": "793dd4558cab33a15635c87ae6157b75d767fadd",
  "bookmarks": [{
  "bookmark": "bm1",
  "node": "b8c2ad26671f334ec09767ea7505c5253863232b",
  "date": [0.0, 0]
  }, {
  "bookmark": "bm2",
  "node": "793dd4558cab33a15635c87ae6157b75d767fadd",
  "date": [0.0, 0]
  }]
  }

Push a bookmark update

  $ echo bm2_2 > foo
  $ hg commit -m 'bm2 commit 2'
  $ hg log -r tip
  changeset:   3:95fa38d78880
  bookmark:    bm2
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     bm2 commit 2
  

  $ hg push -B bm2
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in \d+\.\ds (re)
  remote: replication of bookmarks data completed successfully in \d+\.\ds (re)
  remote: replication of changegroup data completed successfully in \d+\.\ds (re)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/95fa38d78880
  updating bookmark bm2

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-bookmarks
  200
  
  {
  "node": "95fa38d78880f6d477de646b441e7ca4c5ca7015",
  "bookmarks": [{
  "bookmark": "bm1",
  "node": "b8c2ad26671f334ec09767ea7505c5253863232b",
  "date": [0.0, 0]
  }, {
  "bookmark": "bm2",
  "node": "95fa38d78880f6d477de646b441e7ca4c5ca7015",
  "date": [0.0, 0]
  }]
  }

Push a non-forward bookmark update
TODO this is currently buggy: bmo2@default should not exist

  $ hg up -r 1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bm2)
  $ hg bookmark -f bm2
  $ hg push -B bm2
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  no changes found
  remote: replication of bookmarks data completed successfully in \d+\.\ds (re)
  updating bookmark bm2
  [1]

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-bookmarks
  200
  
  {
  "node": "95fa38d78880f6d477de646b441e7ca4c5ca7015",
  "bookmarks": [{
  "bookmark": "bm1",
  "node": "b8c2ad26671f334ec09767ea7505c5253863232b",
  "date": [0.0, 0]
  }, {
  "bookmark": "bm2",
  "node": "95fa38d78880f6d477de646b441e7ca4c5ca7015",
  "date": [0.0, 0]
  }, {
  "bookmark": "bm2@default",
  "node": "b8c2ad26671f334ec09767ea7505c5253863232b",
  "date": [0.0, 0]
  }]
  }

Cleanup

  $ cd ..
  $ hgmo stop
