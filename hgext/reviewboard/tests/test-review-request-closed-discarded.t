#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ bugzilla create-bug TestProduct TestComponent summary

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 2 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish $HGPORT1 1
  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/x-review-board-request
      data: http://localhost:$HGPORT1/r/1/
      description: 'MozReview Request: bz://1/mynick'
      file_name: reviewboard-1-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: bz://1/mynick'
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
        /r/3 - Bug 1 - Foo 2
  
  
        Pull down these commits:
  
  
        hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Close the squashed review request as discarded, which should close all of the
child review requests.

  $ rbmanage closediscarded $HGPORT1 1

Squashed review request with ID 1 should be closed as discarded and have
no Commit ID set.

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be closed as discarded...

  $ rbmanage dumpreview $HGPORT1 2
  id: 2
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be closed as discarded...

  $ rbmanage dumpreview $HGPORT1 3
  id: 3
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

The review attachment should be marked as obsolete

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/x-review-board-request
      data: http://localhost:$HGPORT1/r/1/
      description: 'MozReview Request: bz://1/mynick'
      file_name: reviewboard-1-url.txt
      flags: []
      id: 1
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: bz://1/mynick'
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
        /r/3 - Bug 1 - Foo 2
  
  
        Pull down these commits:
  
  
        hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Re-opening the parent review request should re-open all of the children,
and they should be non-public.

  $ rbmanage reopen $HGPORT1 1

Squashed review request with ID 1 should be re-opened and have its
Commit ID re-instated.

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: pending
  public: false
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
  - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
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
    - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo
    target_people: []
    extra:
      p2rb: true
      p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
        "3"]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs: []

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 2
  id: 2
  status: pending
  public: false
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
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
      p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: false
    diffs: []

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview $HGPORT1 3
  id: 3
  status: pending
  public: false
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
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
      p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: false
    diffs: []

There should still not be a visible attachment on the bug

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/x-review-board-request
      data: http://localhost:$HGPORT1/r/1/
      description: 'MozReview Request: bz://1/mynick'
      file_name: reviewboard-1-url.txt
      flags: []
      id: 1
      is_obsolete: true
      is_patch: false
      summary: 'MozReview Request: bz://1/mynick'
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
        /r/3 - Bug 1 - Foo 2
  
  
        Pull down these commits:
  
  
        hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Should be able to publish these review requests again by publishing the
squashed review request.

  $ rbmanage publish $HGPORT1 1

Squashed review request should be published.

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: pending
  public: true
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
  - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be published.

  $ rbmanage dumpreview $HGPORT1 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be published.

  $ rbmanage dumpreview $HGPORT1 3
  id: 3
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

The attachment for the review request should be unobsoleted

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/x-review-board-request
      data: http://localhost:$HGPORT1/r/1/
      description: 'MozReview Request: bz://1/mynick'
      file_name: reviewboard-1-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: bz://1/mynick'
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
        /r/3 - Bug 1 - Foo 2
  
  
        Pull down these commits:
  
  
        hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo'
    - author: admin@example.com
      id: 3
      tags: []
      text: 'Comment on attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
        /r/3 - Bug 1 - Foo 2
  
  
        Pull down these commits:
  
  
        hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://localhost:$HGPORT/test-repo'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: summary

Cleanup

  $ mozreview stop
  stopped 5 containers
