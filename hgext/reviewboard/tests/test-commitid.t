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

  $ hg log -T '{rev}:{node|short} {desc}\n'
  1:306d1563179b commit 1
  
  MozReview-Commit-ID: 124Bxg
  0:96ee1d7354c4 initial

Mercurial doesn't preserve extras on rebase by default. Verify our
monkeypatch works.

  $ hg -q up -r 0
  $ touch bar
  $ hg -q commit -A -m 'head 2'

  $ hg rebase -s 1 -d 2
  rebasing 1:306d1563179b "commit 1"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/*-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {desc}\n'
  o  2:ae4a1eb0e7a0 commit 1
  |
  |  MozReview-Commit-ID: 124Bxg
  @  1:8a14d300d449 head 2
  |
  |  MozReview-Commit-ID: 5ijR9k
  o  0:96ee1d7354c4 initial
  

Histedit should preserve commit ids when changesets are updated

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

  $ hg log -G -T '{rev}:{node|short} {desc}\n' -r '::.'
  @  5:0aa5a5b9a166 histedit3
  |
  |  MozReview-Commit-ID: JmjAjw
  o  4:bb89e4592815 histedit2
  |
  |  MozReview-Commit-ID: F63vXs
  o  3:4a17019033eb histedit1
  |
  |  MozReview-Commit-ID: APOgLo
  o  0:96ee1d7354c4 initial
  

  $ cat >> commands << EOF
  > p 4a17019033eb
  > p 0aa5a5b9a166
  > p bb89e4592815
  > EOF

  $ hg histedit -r 4a17019033eb --commands commands
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/bb89e4592815-c4460a5c-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {desc}\n' -r '::.'
  @  5:986c4bf069fe histedit2
  |
  |  MozReview-Commit-ID: F63vXs
  o  4:84bc2f59c8ec histedit3
  |
  |  MozReview-Commit-ID: JmjAjw
  o  3:4a17019033eb histedit1
  |
  |  MozReview-Commit-ID: APOgLo
  o  0:96ee1d7354c4 initial
  

Graft will preserve commit id.

  $ hg -q up -r 0
  $ hg graft -r 84bc2f59c8ec
  grafting 4:84bc2f59c8ec "histedit3"

  $ hg log -G -T '{rev}:{node|short} {desc}\n' -r '::.'
  @  6:7eb940c47356 histedit3
  |
  |  MozReview-Commit-ID: JmjAjw
  o  0:96ee1d7354c4 initial
  
