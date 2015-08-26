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

We should not install the rebase extension if it is explicitly set to
disabled

  $ hg --config extensions.rebase=! rebase
  hg: unknown command 'rebase'
  'rebase' is provided by the following extension:
  
      rebase        command to move sets of revisions to a different ancestor
  
  (use "hg help extensions" for information on enabling extensions)
  [255]

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

Mercurial doesn't preserve extras on rebase by default. Verify our
monkeypatch works.

  $ hg -q up -r 0
  $ touch bar
  $ hg -q commit -A -m 'head 2'

  $ hg rebase -s 1 -d 2
  rebasing 1:f649433beb75 "commit 1"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/*-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n'
  o  2:97e57e2cc32f 124Bxg commit 1
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
  @  5:bc98e6acc675 JmjAjw histedit3
  |
  o  4:b7a2d48fe04e F63vXs histedit2
  |
  o  3:5280b158e76d APOgLo histedit1
  |
  o  0:96ee1d7354c4  initial
  

  $ cat >> commands << EOF
  > p 5280b158e76d
  > p bc98e6acc675
  > p b7a2d48fe04e
  > EOF

  $ hg histedit -r 5280b158e76d --commands commands
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/b7a2d48fe04e*-backup.hg (glob)

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n' -r '::.'
  @  5:880ef5832635 F63vXs histedit2
  |
  o  4:412f42129824 JmjAjw histedit3
  |
  o  3:5280b158e76d APOgLo histedit1
  |
  o  0:96ee1d7354c4  initial
  

Graft will preserve commitid.
TODO this doesn't work as expected.

  $ hg -q up -r 0
  $ hg graft -r 412f42129824
  grafting 4:412f42129824 "histedit3"

  $ hg log -G -T '{rev}:{node|short} {get(extras, "commitid")} {desc}\n' -r '::.'
  @  6:8d7c35d9bfd2 OTOPw0 histedit3
  |
  o  0:96ee1d7354c4  initial
  
