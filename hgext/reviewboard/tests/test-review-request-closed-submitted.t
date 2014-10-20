#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-review-request-closed-submitted
  $ bugzilla create-bug-range TestProduct TestComponent 123
  created 123 bugs

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
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:9d24f6cb513e
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

  $ rbmanage publish $HGPORT1 1

Close the squashed review request as submitted, which should close all of the
child review requests.

  $ rbmanage ../rbserver closesubmitted $HGPORT1 1

Squashed review request with ID 1 should be closed as submitted...

  $ rbmanage dumpreview $HGPORT1 1
  Review: 1
    Status: submitted
    Public: True
    Bugs: 123
    Commit ID: bz://123/mynick
    Summary: bz://123/mynick
    Description:
      /r/2 - Bug 123 - Foo 1
      /r/3 - Bug 123 - Foo 2
      
      Pull down these commits:
      
      hg pull review -r 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
      
    Extra:
      p2rb: True
      p2rb.commits: [["bb41178fa30c323500834d0368774ef4ed412d7b", "2"], ["9d24f6cb513e7a5b4e19b684e863304b47dfe4c9", "3"]]
      p2rb.discard_on_publish_rids: []
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
      p2rb.unpublished_rids: []

Child review request with ID 2 should be closed as submitted...

  $ rbmanage dumpreview $HGPORT1 2
  Review: 2
    Status: submitted
    Public: True
    Bugs: 123
    Commit ID: None
    Summary: Bug 123 - Foo 1
    Description:
      Bug 123 - Foo 1
    Extra:
      p2rb: True
      p2rb.commit_id: bb41178fa30c323500834d0368774ef4ed412d7b
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

Child review request with ID 3 should be closed as submitted...

  $ rbmanage dumpreview $HGPORT1 3
  Review: 3
    Status: submitted
    Public: True
    Bugs: 123
    Commit ID: None
    Summary: Bug 123 - Foo 2
    Description:
      Bug 123 - Foo 2
    Extra:
      p2rb: True
      p2rb.commit_id: 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

Re-opening the parent review request should re-open all of the children.

  $ rbmanage ../rbserver reopen $HGPORT1 1

Squashed review request with ID 1 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 1
  Review: 1
    Status: pending
    Public: True
    Bugs: 123
    Commit ID: bz://123/mynick
    Summary: bz://123/mynick
    Description:
      /r/2 - Bug 123 - Foo 1
      /r/3 - Bug 123 - Foo 2
      
      Pull down these commits:
      
      hg pull review -r 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
      
    Extra:
      p2rb: True
      p2rb.commits: [["bb41178fa30c323500834d0368774ef4ed412d7b", "2"], ["9d24f6cb513e7a5b4e19b684e863304b47dfe4c9", "3"]]
      p2rb.discard_on_publish_rids: []
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: True
      p2rb.unpublished_rids: []

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 2
  Review: 2
    Status: pending
    Public: True
    Bugs: 123
    Commit ID: None
    Summary: Bug 123 - Foo 1
    Description:
      Bug 123 - Foo 1
    Extra:
      p2rb: True
      p2rb.commit_id: bb41178fa30c323500834d0368774ef4ed412d7b
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 3
  Review: 3
    Status: pending
    Public: True
    Bugs: 123
    Commit ID: None
    Summary: Bug 123 - Foo 2
    Description:
      Bug 123 - Foo 2
    Extra:
      p2rb: True
      p2rb.commit_id: 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
      p2rb.identifier: bz://123/mynick
      p2rb.is_squashed: False

  $ cd ..
  $ rbmanage rbserver stop
  $ dockercontrol stop-bmo rb-test-review-request-closed-submitted > /dev/null
