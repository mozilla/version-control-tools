#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ bugzilla create-bug TestProduct TestComponent summary

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/61e2e5c813d2*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:233b570e5356
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish 1
  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 1'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 1'
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/3/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 2'
      file_name: reviewboard-3-url.txt
      flags: []
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 2'
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: Bug 1 - Foo 1
  
  
        Bug 1 - Foo 1'
    - author: default@example.com
      id: 3
      tags: []
      text: 'Created attachment 2
  
        MozReview Request: Bug 1 - Foo 2
  
  
        Bug 1 - Foo 2'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Close the squashed review request as discarded, which should close all of the
child review requests.

  $ rbmanage closediscarded 1

Squashed review request with ID 1 should be closed as discarded and have
no Commit ID set.

  $ rbmanage dumpreview 1
  id: 1
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 233b570e5356d0c84bcbf0633de446172012b3b3 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be closed as discarded...

  $ rbmanage dumpreview 2
  id: 2
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be closed as discarded...

  $ rbmanage dumpreview 3
  id: 3
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

The review attachment should be marked as obsolete

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 1'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 1'
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/3/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 2'
      file_name: reviewboard-3-url.txt
      flags: []
      id: 2
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 2'
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: Bug 1 - Foo 1
  
  
        Bug 1 - Foo 1'
    - author: default@example.com
      id: 3
      tags: []
      text: 'Created attachment 2
  
        MozReview Request: Bug 1 - Foo 2
  
  
        Bug 1 - Foo 2'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Re-opening the parent review request should re-open all of the children,
and they should be non-public.

  $ rbmanage reopen 1

Squashed review request with ID 1 should be re-opened and have its
Commit ID re-instated.

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: false
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 233b570e5356d0c84bcbf0633de446172012b3b3 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description:
    - /r/2 - Bug 1 - Foo 1
    - /r/3 - Bug 1 - Foo 2
    - ''
    - 'Pull down these commits:'
    - ''
    - hg pull -r 233b570e5356d0c84bcbf0633de446172012b3b3 http://*:$HGPORT/test-repo (glob)
    target_people: []
    extra:
      p2rb: true
      p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
        3]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{}'
      p2rb.unpublished_rids: '[]'
    diffs: []

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: false
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  draft:
    bugs:
    - '1'
    commit: null
    summary: Bug 1 - Foo 1
    description: Bug 1 - Foo 1
    target_people: []
    extra:
      p2rb: true
      p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: false
    diffs: []

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview 3
  id: 3
  status: pending
  public: false
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  draft:
    bugs:
    - '1'
    commit: null
    summary: Bug 1 - Foo 2
    description: Bug 1 - Foo 2
    target_people: []
    extra:
      p2rb: true
      p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: false
    diffs: []

There should still not be a visible attachment on the bug

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 1'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 1'
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/3/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 2'
      file_name: reviewboard-3-url.txt
      flags: []
      id: 2
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 2'
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: Bug 1 - Foo 1
  
  
        Bug 1 - Foo 1'
    - author: default@example.com
      id: 3
      tags: []
      text: 'Created attachment 2
  
        MozReview Request: Bug 1 - Foo 2
  
  
        Bug 1 - Foo 2'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Should be able to publish these review requests again by publishing the
squashed review request.

  $ rbmanage publish 1

Squashed review request should be published.

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 233b570e5356d0c84bcbf0633de446172012b3b3 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be published.

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be published.

  $ rbmanage dumpreview 3
  id: 3
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

The attachment for the review request should be unobsoleted

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 1'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 1'
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/3/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 2'
      file_name: reviewboard-3-url.txt
      flags: []
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 2'
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: Bug 1 - Foo 1
  
  
        Bug 1 - Foo 1'
    - author: default@example.com
      id: 3
      tags: []
      text: 'Created attachment 2
  
        MozReview Request: Bug 1 - Foo 2
  
  
        Bug 1 - Foo 2'
    - author: default@example.com
      id: 4
      tags: []
      text: 'Comment on attachment 1
  
        MozReview Request: Bug 1 - Foo 1
  
  
        Bug 1 - Foo 1'
    - author: default@example.com
      id: 5
      tags: []
      text: 'Comment on attachment 2
  
        MozReview Request: Bug 1 - Foo 2
  
  
        Bug 1 - Foo 2'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Cleanup

  $ mozreview stop
  stopped 8 containers
