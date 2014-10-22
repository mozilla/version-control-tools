#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv rb-test-bugzilla-review-interaction

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ bugzilla create-user author@example.com password 'Some Contributor'
  created user 2
  $ bugzilla create-user reviewer@example.com password 'Mozilla Reviewer [:reviewer]'
  created user 3
  $ bugzilla create-user reviewer2@example.com password 'Another Reviewer [:rev2]'
  created user 4

Create a review request from a regular user

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push http://localhost:$HGPORT/ > /dev/null

Adding a reviewer should result in a r? flag being set

  $ rbmanage add-reviewer $HGPORT1 1 --user reviewer
  1 people listed on review request
  $ rbmanage publish $HGPORT1 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://example.com/r/1/
      description: 'MozReview Request: bz://1/mynick'
      flags:
      - id: 1
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 1
      summary: 'MozReview Request: bz://1/mynick'
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick'
    - author: author@example.com
      id: 3
      tags: []
      text: '/r/2 - Bug 1 - Initial commit to review
  
  
        Pull down this commit:
  
  
        hg pull review -r 57755461e85f1e3e66738ec2d57f325249897409'
    summary: First Bug

Adding a "Ship It" review will grant r+

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review $HGPORT1 1 --body-top LGTM --public --ship-it
  created review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://example.com/r/1/
      description: 'MozReview Request: bz://1/mynick'
      flags:
      - id: 1
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      summary: 'MozReview Request: bz://1/mynick'
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick'
    - author: author@example.com
      id: 3
      tags: []
      text: '/r/2 - Bug 1 - Initial commit to review
  
  
        Pull down this commit:
  
  
        hg pull review -r 57755461e85f1e3e66738ec2d57f325249897409'
    - author: reviewer@example.com
      id: 4
      tags: []
      text: 'http://example.com/r/1/#review1
  
  
        LGTM'
    summary: First Bug

Adding a reply to the review will add a comment to Bugzilla

  $ exportbzauth author@example.com password
  $ rbmanage create-review-reply $HGPORT1 1 1 --body-bottom 'Thanks!' --public
  created review reply 2

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://example.com/r/1/
      description: 'MozReview Request: bz://1/mynick'
      flags:
      - id: 1
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      summary: 'MozReview Request: bz://1/mynick'
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        MozReview Request: bz://1/mynick'
    - author: author@example.com
      id: 3
      tags: []
      text: '/r/2 - Bug 1 - Initial commit to review
  
  
        Pull down this commit:
  
  
        hg pull review -r 57755461e85f1e3e66738ec2d57f325249897409'
    - author: reviewer@example.com
      id: 4
      tags: []
      text: 'http://example.com/r/1/#review1
  
  
        LGTM'
    - author: author@example.com
      id: 5
      tags: []
      text: 'http://example.com/r/1/#review2
  
  
        Thanks!'
    summary: First Bug

Ensure multiple reviewers works as expected

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Multiple Reviewers'

  $ hg up -r 0 > /dev/null
  $ echo b2 > foo
  $ hg commit -m 'Bug 2 - Multiple reviewers'
  created new head
  $ hg --config bugzilla.username=author@example.com push http://localhost:$HGPORT/ > /dev/null

  $ rbmanage add-reviewer $HGPORT1 3 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage publish $HGPORT1 3

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://example.com/r/3/
      description: 'MozReview Request: bz://2/mynick'
      flags:
      - id: 3
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 4
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 2
      summary: 'MozReview Request: bz://2/mynick'
    comments:
    - author: author@example.com
      id: 6
      tags: []
      text: ''
    - author: author@example.com
      id: 7
      tags: []
      text: 'Created attachment 2
  
        MozReview Request: bz://2/mynick'
    - author: author@example.com
      id: 8
      tags: []
      text: '/r/4 - Bug 2 - Multiple reviewers
  
  
        Pull down this commit:
  
  
        hg pull review -r d17099d7ee43e288f43e0210edc71b9782f92b77'
    summary: Multiple Reviewers

  $ cd ..

Cleanup

  $ rbmanage stop rbserver
  $ dockercontrol stop-bmo rb-test-bugzilla-review-interaction
  stopped 2 containers
