  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF
  $ echo obs "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

  $ cd client
  $ echo 'foo' > foo0
  $ hg commit -A -m 'root commit'
  adding foo0
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 123 - Foo 1'
  adding foo1
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 123 - Foo 2'
  adding foo2
  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 123 - Foo 3'
  adding foo3
  $ echo 'foo4' > foo4
  $ hg commit -A -m 'Bug 123 - Foo 4'
  adding foo4
  $ echo 'foo5' > foo5
  $ hg commit -A -m 'Bug 123 - Foo 5'
  adding foo5

  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 5 changes to 5 files
  submitting 5 changesets for review
  
  changeset:  1:c5b850e24951
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:905ad211ecc6
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  3:68fdf92dbf14
  summary:    Bug 123 - Foo 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  changeset:  4:53b32d356f20
  summary:    Bug 123 - Foo 4
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  changeset:  5:f466ed1de516
  summary:    Bug 123 - Foo 5
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

Popping the last commit truncates the review set

  $ hg strip -r 5 --no-backup
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 4 changesets for review
  
  changeset:  1:c5b850e24951
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:905ad211ecc6
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  3:68fdf92dbf14
  summary:    Bug 123 - Foo 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  changeset:  4:53b32d356f20
  summary:    Bug 123 - Foo 4
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  [1]

The parent review should have dropped the reference to /r/6

  $ rbmanage ../rbserver dumpreview $HGPORT1 1
  Review: 1
    Status: pending
    Commit ID: bz://123/mynick
    Extra:
      p2rb: True
      p2rb.commits: [["c5b850e249510046906bcb24f774635c4521a4a9", "2"], ["905ad211ecc6f024e1f0ffdbe084dd06cf28ae1c", "3"], ["68fdf92dbf149ab8afb8295a76b79fb82a9629b1", "4"], ["53b32d356f20f6730c14ec62c3706eba7e68e078", "5"]]
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
  Draft: 1
    Commit ID: bz://123/mynick
    Summary: Review for review ID: bz://123/mynick
    Description:
      /r/2 - Bug 123 - Foo 1
      /r/3 - Bug 123 - Foo 2
      /r/4 - Bug 123 - Foo 3
      /r/5 - Bug 123 - Foo 4
      
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
  Diff: 7
    Revision: 1
  diff -r 93d9429b41ec -r 53b32d356f20 foo1
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo1	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo1
  diff -r 93d9429b41ec -r 53b32d356f20 foo2
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo2	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo2
  diff -r 93d9429b41ec -r 53b32d356f20 foo3
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo3	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo3
  diff -r 93d9429b41ec -r 53b32d356f20 foo4
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo4	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo4
  

Review 6 should be marked as discarded

  $ rbmanage ../rbserver dumpreview $HGPORT1 6
  Review: 6
    Status: discarded
    Commit ID: f466ed1de51670e583e11deb2f1022a342b52ccd
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False
  Draft: 6
    Commit ID: f466ed1de51670e583e11deb2f1022a342b52ccd
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

Dropping the first commit should drop its review. Subsequent reviews should
be preserved.

  $ hg rebase -s 2 -d 0
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 0 changes to 0 files (+1 heads)
  submitting 3 changesets for review
  
  changeset:  5:ce44f0c4506c
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  6:2879da44c7e2
  summary:    Bug 123 - Foo 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  changeset:  7:e44f9d56a1a4
  summary:    Bug 123 - Foo 4
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

The dropped commit should now be discarded

  $ rbmanage ../rbserver dumpreview $HGPORT1 2
  Review: 2
    Status: discarded
    Commit ID: c5b850e249510046906bcb24f774635c4521a4a9
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False
  Draft: 7
    Commit ID: c5b850e249510046906bcb24f774635c4521a4a9
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

Try removing a commit in the middle.

  $ hg rebase -s e44f9d56a1a4 -d ce44f0c4506c
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 0 files (+1 heads)
  submitting 2 changesets for review
  
  changeset:  5:ce44f0c4506c
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  8:cd0051d388da
  summary:    Bug 123 - Foo 4
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

The parent review should have been updated accordingly.

  $ rbmanage ../rbserver dumpreview $HGPORT1 1
  Review: 1
    Status: pending
    Commit ID: bz://123/mynick
    Extra:
      p2rb: True
      p2rb.commits: [["ce44f0c4506c2e377ccfb702277cec50905be3e3", "3"], ["cd0051d388dabe9694e0e2c5ce1cdbb17749c53d", "5"]]
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
  Draft: 1
    Commit ID: bz://123/mynick
    Summary: Review for review ID: bz://123/mynick
    Description:
      /r/3 - Bug 123 - Foo 2
      /r/5 - Bug 123 - Foo 4
      
    Extra:
      p2rb: True
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
  Diff: 12
    Revision: 1
  diff -r 93d9429b41ec -r cd0051d388da foo2
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo2	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo2
  diff -r 93d9429b41ec -r cd0051d388da foo4
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo4	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo4
  
