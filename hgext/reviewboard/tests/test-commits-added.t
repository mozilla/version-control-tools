  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 123 - Foo 1'
  $ echo 'foo2' > foo
  $ hg commit -m 'Bug 123 - Foo 2'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 2 changesets for review
  
  changeset:  1:bb41178fa30c
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2
  
  changeset:  2:9d24f6cb513e
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3
  
  review id:  bz://123
  review url: http://localhost:$HGPORT1/r/1

Adding commits to old reviews should create new reviews

  $ echo 'foo3' > foo
  $ hg commit -m 'Bug 123 - Foo 3'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 3 changesets for review
  
  changeset:  1:bb41178fa30c
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2
  
  changeset:  2:9d24f6cb513e
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3
  
  changeset:  3:27d2e8c43375
  summary:    Bug 123 - Foo 3
  review:     http://localhost:$HGPORT1/r/4
  
  review id:  bz://123
  review url: http://localhost:$HGPORT1/r/1

The parent review should have its description updated.

  $ rbmanage ../rbserver dumpreview $HGPORT1 1
  Review: 1
    Status: pending
    Commit ID: bz://123
    Extra:
      p2rb: True
      p2rb.commits: [["bb41178fa30c323500834d0368774ef4ed412d7b", "2"], ["9d24f6cb513e7a5b4e19b684e863304b47dfe4c9", "3"], ["27d2e8c43375f3dd075cd7492a1f301ecdca9ffc", "4"]]
      p2rb.identifier: bz://123
      p2rb.is_squashed: True
  Draft: 1
    Commit ID: bz://123
    Summary: Review for review ID: bz://123
    Description:
      /r/2 - Bug 123 - Foo 1
      /r/3 - Bug 123 - Foo 2
      /r/4 - Bug 123 - Foo 3
      
    Extra:
      p2rb: True
      p2rb.identifier: bz://123
      p2rb.is_squashed: True
  Diff: 4
    Revision: 1
  diff -r 7c5bdf0cec4a -r 27d2e8c43375 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo0
  +foo3
  
