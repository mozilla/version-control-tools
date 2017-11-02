#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

Pushing a review should not touch Bugzilla

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ bugzilla create-bug TestProduct TestComponent bug2

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/24417bc94b2c*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:98467d80785e
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ bugzilla dump-bug 1
  Bug 1:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Publishing the review will add an attachment to the bug

  $ rbmanage publish 1
  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Foo 1
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Foo 1
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 3
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

We should only display the full commit description the first time it is
published.

  $ echo foo1 >> foo
  $ hg commit --amend
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/98467d80785e-*.hg (glob)
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:c84f52fcaead
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage publish 1
  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Foo 1
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Foo 1
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 3
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: default@example.com
      id: 4
      tags:
      - mozreview-request
      text:
      - Comment on attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

We should not post an interdiff link if there are no code changes. This
can happen if a reviewer is manually added (see Bug 1229789).

  $ mozreview create-user reviewer@example.com password1 'Mozilla Reviewer [:reviewer]' --bugzilla-group editbugs
  Created user 6
  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1
  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Foo 1
      file_name: reviewboard-2-url.txt
      flags:
      - id: 1
        name: review
        requestee: reviewer@example.com
        setter: default@example.com
        status: '?'
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Foo 1
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 3
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: default@example.com
      id: 4
      tags:
      - mozreview-request
      text:
      - Comment on attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Ensure r? in the commit description sets a review flag when pushing

  $ echo foo2 > foo
  $ hg commit -m 'Bug 2 - Foo 1 r?reviewer'
  $ hg push --config reviewboard.autopublish=true -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/12f973a4cce5-aff74ce2-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  2:f9979978463c
  summary:    Bug 2 - Foo 1 r?reviewer
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  (published review request 3)

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: Bug 2 - Foo 1
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: reviewer@example.com
        setter: default@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 2 - Foo 1
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: default@example.com
      id: 2
      tags: []
      text: ''
    - author: default@example.com
      id: 5
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 2 - Foo 1
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug2

  $ mozreview stop
  stopped 9 containers
