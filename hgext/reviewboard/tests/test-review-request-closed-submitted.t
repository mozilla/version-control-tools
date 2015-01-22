#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-review-request-closed-submitted
  $ bugzilla create-bug-range TestProduct TestComponent 123
  created bugs 1 to 123

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
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish $HGPORT1 1

Close the squashed review request as submitted, which should close all of the
child review requests.

  $ rbmanage closesubmitted $HGPORT1 1

Squashed review request with ID 1 should be closed as submitted...

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: submitted
  public: true
  bugs:
  - '123'
  commit: bz://123/mynick
  summary: bz://123/mynick
  description:
  - /r/2 - Bug 123 - Foo 1
  - /r/3 - Bug 123 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9 http://localhost:$HGPORT/
  extra_data:
    p2rb: true
    p2rb.commits: '[["bb41178fa30c323500834d0368774ef4ed412d7b", "2"], ["9d24f6cb513e7a5b4e19b684e863304b47dfe4c9",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be closed as submitted...

  $ rbmanage dumpreview $HGPORT1 2
  id: 2
  status: submitted
  public: true
  bugs:
  - '123'
  commit: null
  summary: Bug 123 - Foo 1
  description: Bug 123 - Foo 1
  extra_data:
    p2rb: true
    p2rb.commit_id: bb41178fa30c323500834d0368774ef4ed412d7b
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: false

  $ rbmanage dumpreview $HGPORT1 3
  id: 3
  status: submitted
  public: true
  bugs:
  - '123'
  commit: null
  summary: Bug 123 - Foo 2
  description: Bug 123 - Foo 2
  extra_data:
    p2rb: true
    p2rb.commit_id: 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: false

Re-opening the parent review request should re-open all of the children.

  $ rbmanage reopen $HGPORT1 1

Squashed review request with ID 1 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: pending
  public: true
  bugs:
  - '123'
  commit: bz://123/mynick
  summary: bz://123/mynick
  description:
  - /r/2 - Bug 123 - Foo 1
  - /r/3 - Bug 123 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9 http://localhost:$HGPORT/
  extra_data:
    p2rb: true
    p2rb.commits: '[["bb41178fa30c323500834d0368774ef4ed412d7b", "2"], ["9d24f6cb513e7a5b4e19b684e863304b47dfe4c9",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 2
  id: 2
  status: pending
  public: true
  bugs:
  - '123'
  commit: null
  summary: Bug 123 - Foo 1
  description: Bug 123 - Foo 1
  extra_data:
    p2rb: true
    p2rb.commit_id: bb41178fa30c323500834d0368774ef4ed412d7b
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 3
  id: 3
  status: pending
  public: true
  bugs:
  - '123'
  commit: null
  summary: Bug 123 - Foo 2
  description: Bug 123 - Foo 2
  extra_data:
    p2rb: true
    p2rb.commit_id: 9d24f6cb513e7a5b4e19b684e863304b47dfe4c9
    p2rb.identifier: bz://123/mynick
    p2rb.is_squashed: false

  $ cd ..
  $ rbmanage stop rbserver
  $ dockercontrol stop-bmo rb-test-review-request-closed-submitted
  stopped 3 containers
