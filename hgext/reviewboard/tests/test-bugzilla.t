#require docker
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
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/24417bc94b2c*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

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
      data: http://*:$HGPORT1/r/2/ (glob)
      description: 'MozReview Request: Bug 1 - Foo 1'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Foo 1'
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 3
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Foo 1'
      - ''
      - Bug 1 - Foo 1
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

  $ mozreview stop
  stopped 8 containers
