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
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ bugzilla dump-bug 1
  Bug 1:
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
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
      id: 3
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick
  
  
        /r/2 - Bug 1 - Foo 1
  
  
        Pull down this commit:
  
  
        hg pull -r 24417bc94b2c053e8f5dd8c09da33fbbef5404fe http://localhost:$HGPORT/test-repo'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

  $ mozreview stop
  stopped 5 containers
