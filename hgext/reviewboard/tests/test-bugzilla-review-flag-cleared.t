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
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} push > /dev/null 2>&1

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
      description: Bug 1 - Initial commit to review
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
      summary: Bug 1 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Initial commit to review
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

Publishing a non-'clear-the-flag' review will not clear the r? flag

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 2 --body-top 'I have reservations' --public
  created review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Initial commit to review
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
      summary: Bug 1 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
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

Posting an r? review with a comment only adds a comment

  $ rbmanage create-review 2 --body-top 'One more thing...' --public
  created review 2

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Initial commit to review
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
      summary: Bug 1 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
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

Posting a r+ review will add a '+' review flag

  $ rbmanage create-review 2 --body-top LGTM --public --review-flag='r+'
  created review 3

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Initial commit to review
      file_name: reviewboard-2-url.txt
      flags:
      - id: 1
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - One more thing...
    - author: reviewer@example.com
      id: 5
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
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
      description: Bug 1 - Initial commit to review
      file_name: reviewboard-2-url.txt
      flags:
      - id: 1
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: reviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - I have reservations
    - author: reviewer@example.com
      id: 4
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - One more thing...
    - author: reviewer@example.com
      id: 5
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review3
      - ''
      - LGTM
    - author: author@example.com
      id: 6
      tags:
      - mozreview-request
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
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
  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=${l3key} push > /dev/null 2>&1

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
      description: Bug 2 - Initial commit to review
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: reviewer@example.com
        setter: l3author@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 2 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 2 - Initial commit to review
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
  $ rbmanage create-review 4 --body-top LGTM --public --review-flag='r+'
  created review 4

Sanity check to ensure we have an r+ flag set

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: l3author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: Bug 2 - Initial commit to review
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 2 - Initial commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 2 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    - author: reviewer@example.com
      id: 9
      tags:
      - mozreview-review
      text:
      - Comment on attachment 2
      - Bug 2 - Initial commit to review
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
      description: Bug 2 - Modified commit to review
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 2 - Modified commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    - author: reviewer@example.com
      id: 9
      tags:
      - mozreview-review
      text:
      - Comment on attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/4/#review4
      - ''
      - LGTM
    - author: l3author@example.com
      id: 10
      tags:
      - mozreview-request
      text:
      - Comment on attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Second Bug

Posting a r- review will add a '-' review flag

  $ rbmanage create-review 4 --body-top 'I changed my mind' --public --review-flag='r-'
  created review 5
  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: l3author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header
      description: Bug 2 - Modified commit to review
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      - id: 3
        name: review
        requestee: null
        setter: l3author@example.com
        status: '-'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 2 - Modified commit to review
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
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/'
    - author: reviewer@example.com
      id: 9
      tags:
      - mozreview-review
      text:
      - Comment on attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/4/#review4
      - ''
      - LGTM
    - author: l3author@example.com
      id: 10
      tags:
      - mozreview-request
      text:
      - Comment on attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/4/diff/1-2/'
    - author: l3author@example.com
      id: 11
      tags:
      - mozreview-review
      text:
      - Comment on attachment 2
      - Bug 2 - Modified commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/4/#review5
      - ''
      - I changed my mind
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Second Bug

Adding a reviewer should leave r- untouched

  $ mozreview create-user reviewer2@example.com password 'Mozilla Reviewer 2 [:reviewer2]' --bugzilla-group editbugs
  Created user 9

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Third Bug'

  $ echo bug3 > foo
  $ hg commit -m 'Bug 3 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} push -c . > /dev/null 2>&1
  $ rbmanage add-reviewer 6 --user reviewer
  1 people listed on review request
  $ rbmanage publish 5

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 6 --body-top 'This is all wrong' --public --review-flag='r-'
  created review 6

  $ exportbzauth author@example.com password
  $ rbmanage add-reviewer 6 --user reviewer2
  2 people listed on review request
  $ rbmanage publish 5
  $ bugzilla dump-bug 3
  Bug 3:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/diff/#index_header
      description: Bug 3 - Initial commit to review
      file_name: reviewboard-6-url.txt
      flags:
      - id: 4
        name: review
        requestee: null
        setter: reviewer@example.com
        status: '-'
      - id: 5
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      id: 3
      is_obsolete: false
      is_patch: false
      summary: Bug 3 - Initial commit to review
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 12
      tags: []
      text: ''
    - author: author@example.com
      id: 13
      tags:
      - mozreview-request
      text:
      - Created attachment 3
      - Bug 3 - Initial commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/'
    - author: reviewer@example.com
      id: 14
      tags:
      - mozreview-review
      text:
      - Comment on attachment 3
      - Bug 3 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/6/#review6
      - ''
      - This is all wrong
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Third Bug

Publishing a new revision should reset r- to r?, and carry forward r+

  $ exportbzauth author@example.com password
  $ echo updated >> foo
  $ hg commit --amend -m 'Bug 3 - Modified commit to review' > /dev/null
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} push -c . > /dev/null 2>&1
  $ bugzilla dump-bug 3
  Bug 3:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/diff/#index_header
      description: Bug 3 - Modified commit to review
      file_name: reviewboard-6-url.txt
      flags:
      - id: 4
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      - id: 5
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      id: 3
      is_obsolete: false
      is_patch: false
      summary: Bug 3 - Modified commit to review
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 12
      tags: []
      text: ''
    - author: author@example.com
      id: 13
      tags:
      - mozreview-request
      text:
      - Created attachment 3
      - Bug 3 - Modified commit to review
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/'
    - author: reviewer@example.com
      id: 14
      tags:
      - mozreview-review
      text:
      - Comment on attachment 3
      - Bug 3 - Modified commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/6/#review6
      - ''
      - This is all wrong
    - author: author@example.com
      id: 15
      tags:
      - mozreview-request
      text:
      - Comment on attachment 3
      - Bug 3 - Modified commit to review
      - ''
      - 'Review request updated; see interdiff: http://$DOCKER_HOSTNAME:$HGPORT1/r/6/diff/1-2/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Third Bug

Cleanup

  $ cd ..
  $ mozreview stop
  stopped 7 containers
