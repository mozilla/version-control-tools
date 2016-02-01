#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m 'root commit'
  $ hg phase --public -r .

  $ mozreview create-user author@example.com password 'Patch Author' --uid 2001 --scm-level 1
  Created user 6
  $ authorkey=`mozreview create-api-key author@example.com`
  $ mozreview create-user reviewer@example.com password 'Mozilla Reviewer [:reviewer]' --bugzilla-group editbugs
  Created user 7

Create a review

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

  $ echo bug > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} push > /dev/null

  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1

Sanity check to ensure we have a review flag set

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags:
      - id: 1
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Publishing a review will clear the r? flag

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 2 --body-top 'I have reservations' --public
  created review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Posting a non Ship It review without a review flag adds a comment

  $ rbmanage create-review 2 --body-top 'One more thing...' --public
  created review 2

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags: []
      text:
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - One more thing...
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Posting a Ship It review will add an r+

  $ rbmanage create-review 2 --body-top LGTM --public --ship-it
  created review 3

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags:
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags: []
      text:
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - One more thing...
    - author: reviewer@example.com
      id: 5
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review3
      - ''
      - LGTM
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Updating the review request as an L1 author will not re-request review

  $ exportbzauth author@example.com password

  $ echo newcontents > foo
  $ hg commit --amend > /dev/null
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} --config reviewboard.autopublish=true push > /dev/null

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: 'MozReview Request: Bug 1 - Initial commit to review'
      file_name: reviewboard-2-url.txt
      flags:
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 1 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags: []
      text:
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - One more thing...
    - author: reviewer@example.com
      id: 5
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review3
      - ''
      - LGTM
    - author: author@example.com
      id: 6
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug


Create a new author with level 3 commit access

  $ mozreview create-user l3author@example.com password 'L3 Contributor'  --uid 2002 --scm-level 3
  Created user 8
  $ l3key=`mozreview create-api-key l3author@example.com`

Create a review

  $ exportbzauth l3author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Second Bug'

  $ hg commit --amend -m 'Bug 2 - Initial commit to review' > /dev/null
  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=${l3key} push > /dev/null

  $ rbmanage add-reviewer 4 --user reviewer
  1 people listed on review request
  $ rbmanage publish 3

Sanity check to ensure we have an r? flag

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: l3author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: 'MozReview Request: Bug 2 - Initial commit to review'
      file_name: reviewboard-4-url.txt
      flags:
      - id: 3
        name: review
        requestee: reviewer@example.com
        setter: l3author@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: l3author@example.com
      id: 7
      tags: []
      text: ''
    - author: l3author@example.com
      id: 8
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Second Bug

Post a Ship It review so we can carry it forward

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 4 --body-top LGTM --public --ship-it
  created review 4

Sanity check to ensure we have an r+ flag set

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: l3author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: 'MozReview Request: Bug 2 - Initial commit to review'
      file_name: reviewboard-4-url.txt
      flags:
      - id: 3
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Initial commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: l3author@example.com
      id: 7
      tags: []
      text: ''
    - author: l3author@example.com
      id: 8
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Initial commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    - author: reviewer@example.com
      id: 9
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Initial commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/4/#review4
      - ''
      - LGTM
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Second Bug

Updating the review request as an L3 author will carry forward the r+

  $ exportbzauth l3author@example.com password

  $ hg commit --amend -m 'Bug 2 - Modified commit to review' > /dev/null

We publish on push since we already have a reviewer

  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=${l3key} --config reviewboard.autopublish=true push > /dev/null

We should have an r+ flag already set.

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: l3author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: 'MozReview Request: Bug 2 - Modified commit to review'
      file_name: reviewboard-4-url.txt
      flags:
      - id: 3
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Modified commit to review'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: l3author@example.com
      id: 7
      tags: []
      text: ''
    - author: l3author@example.com
      id: 8
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Modified commit to review'
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    - author: reviewer@example.com
      id: 9
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Modified commit to review'
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/4/#review4
      - ''
      - LGTM
    - author: l3author@example.com
      id: 10
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Modified commit to review'
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Second Bug

  $ cd ..

Cleanup

  $ mozreview stop
  stopped 10 containers
