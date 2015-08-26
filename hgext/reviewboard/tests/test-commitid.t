  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > histedit =
  > rebase =
  > reviewboard = $TESTDIR/hgext/reviewboard/client.py
  > 
  > [reviewboard]
  > fakeids = true
  > EOF

  $ hg init repo1
  $ cd repo1

  $ touch foo
  $ hg -q commit -A -m initial

Commit IDs are only added for repos known to be associated with
MozReview. Install a dummy review URL to fake it out.

  $ cat >> .hg/reviews << EOF
  > u https://dummy1/
  > r https://dummy2/
  > EOF

Commit ID should be present after review URL is defined.

  $ echo c1 > foo
  $ hg commit -m 'commit 1'

  $ hg log -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n'
  1:f649433beb75 124Bxg commit 1
  0:96ee1d7354c4  initial

Mercurial doesn't preserve extras on rebase by default.
TODO we should fix this.

  $ hg -q up -r 0
  $ touch bar
  $ hg -q commit -A -m 'head 2'

  $ hg rebase -s 1 -d 2
  rebasing 1:f649433beb75 "commit 1"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/*-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n'
  o  2:57ce3354aa4b APOgLo commit 1
  |
  @  1:b3e6f181008c 5ijR9k head 2
  |
  o  0:96ee1d7354c4  initial
  

Histedit should preserve commitids when changesets are updated

  $ hg -q up -r 0
  $ echo 1 > bar
  $ hg commit -A -m histedit1
  adding bar
  created new head
  $ echo 2 > bar
  $ hg commit -m histedit2
  $ echo 3 > baz
  $ hg commit -A -m histedit3
  adding baz

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n' -r '::.'
  @  5:4eac84934e51 OTOPw0 histedit3
  |
  o  4:60dcab4217cd JmjAjw histedit2
  |
  o  3:83b062b39f6e F63vXs histedit1
  |
  o  0:96ee1d7354c4  initial
  

  $ cat >> commands << EOF
  > p 83b062b39f6e
  > p 4eac84934e51
  > p 60dcab4217cd
  > EOF

  $ hg histedit -r 83b062b39f6e --commands commands
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/60dcab4217cd*-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n' -r '::.'
  @  5:ad1499e10a13 JmjAjw histedit2
  |
  o  4:cb4fad627ceb OTOPw0 histedit3
  |
  o  3:83b062b39f6e F63vXs histedit1
  |
  o  0:96ee1d7354c4  initial
  

Graft will preserve commitid.
TODO this doesn't work as expected.

  $ hg -q up -r 0
  $ hg graft -r cb4fad627ceb
  grafting 4:cb4fad627ceb "histedit3"

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n' -r '::.'
  @  6:693d9f47bf53 TA3f84 histedit3
  |
  o  0:96ee1d7354c4  initial
  
