  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > obshacks = $TESTDIR/hgext/obsolescencehacks
  > rebase =
  > [obshacks]
  > obsolescenceexchangeusers = obsenabled1, obsenabled2
  > userfromenv = true
  > EOF

  $ hg init repo0
  $ cat >> repo0/.hg/hgrc << EOF
  > [phases]
  > publish = false
  > EOF
  $ hg init repo1
  $ cat >> repo1/.hg/hgrc << EOF
  > [phases]
  > publish = false
  > [experimental]
  > evolution = createmarkers
  > EOF

  $ cd repo0

Obsolescence should not be enabled by installing the extension

  $ touch foo
  $ hg -q commit -A -m initial
  $ touch file0
  $ hg -q commit -A -m commit0
  $ hg -q up -r 0
  $ touch file1
  $ hg -q commit -A -m commit1
  $ hg rebase -s 1 -d 2
  rebasing 1:b560492eed23 "commit0"
  saved backup bundle to $TESTTMP/repo0/.hg/strip-backup/b560492eed23-664682ca-*.hg (glob)
  $ hg debugobsolete

  $ hg log -G
  o  changeset:   2:f63449cbe54b
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     commit0
  |
  @  changeset:   1:f5c678d0b6b2
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     commit1
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

Enabling obsolescence won't enable marker exchange since the user doesn't match

  $ export USER=noexchange
  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > evolution = createmarkers
  > EOF
  $ hg rebase -s tip -d 0
  rebasing 2:f63449cbe54b "commit0" (tip)

  $ hg debugobsolete
  f63449cbe54b827336a7f1ffc693d3bae1ade0a7 e5c676115f5fcffb7934901030505da37e515075 0 (*) {*'user': 'test'} (glob)

  $ hg log -G
  o  changeset:   3:e5c676115f5f
  |  tag:         tip
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     commit0
  |
  | @  changeset:   1:f5c678d0b6b2
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     commit1
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ hg push ../repo1
  pushing to ../repo1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files (+1 heads)

No markers on destination repo

  $ hg -R ../repo1 debugobsolete

Setting the USER to one in the list will enable marker exchange

  $ export USER=obsenabled2
  $ hg push ../repo1
  pushing to ../repo1
  searching for changes
  no changes found
  1 new obsolescence markers
  [1]

  $ hg -R ../repo1 debugobsolete
  f63449cbe54b827336a7f1ffc693d3bae1ade0a7 e5c676115f5fcffb7934901030505da37e515075 0 (*) {*'user': 'test'} (glob)
