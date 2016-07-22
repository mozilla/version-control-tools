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
  $ mozreview create-user plusreviewer@example.com password 'Mozilla Plus Reviewer [:plusreviewer]' --bugzilla-group editbugs
  Created user 7
  $ mozreview create-user minusreviewer@example.com password 'Mozilla Minus Reviewer [:minusreviewer]' --bugzilla-group editbugs
  Created user 8
  $ mozreview create-user newreviewer@example.com password 'Mozilla New Reviewer [:newreviewer]' --bugzilla-group editbugs
  Created user 9

Create a review

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

  $ echo bug > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} --config reviewboard.autopublish=false push > /dev/null 2>&1

  $ rbmanage add-reviewer 2 --user minusreviewer
  1 people listed on review request
  $ rbmanage add-reviewer 2 --user plusreviewer
  2 people listed on review request
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
        requestee: minusreviewer@example.com
        setter: author@example.com
        status: '?'
      - id: 2
        name: review
        requestee: plusreviewer@example.com
        setter: author@example.com
        status: '?'
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Initial commit to review
    blocks: []
    cc:
    - minusreviewer@example.com
    - plusreviewer@example.com
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

Leave both an r+ and an r-.

  $ exportbzauth plusreviewer@example.com password
  $ rbmanage create-review 2 --body-top 'lgtm' --public --review-flag r+
  created review 1

  $ exportbzauth minusreviewer@example.com password
  $ rbmanage create-review 2 --body-top 'there are problems' --public --review-flag r-
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
        requestee: null
        setter: minusreviewer@example.com
        status: '-'
      - id: 2
        name: review
        requestee: null
        setter: plusreviewer@example.com
        status: +
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Initial commit to review
    blocks: []
    cc:
    - minusreviewer@example.com
    - plusreviewer@example.com
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
    - author: plusreviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - lgtm
    - author: minusreviewer@example.com
      id: 4
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - there are problems
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Update commit, remove original reviewers, and add a new reviewer.

  $ exportbzauth author@example.com password

  $ echo newcontents > foo
  $ hg commit --amend > /dev/null
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} --config reviewboard.autopublish=false push > /dev/null 2>&1

  $ rbmanage remove-reviewer 2 --user minusreviewer --user plusreviewer
  0 people listed on review request
  $ rbmanage add-reviewer 2 --user newreviewer
  1 people listed on review request

  $ rbmanage publish 1

New r? should be added, old r+ and r- should be dropped.

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Initial commit to review
      file_name: reviewboard-2-url.txt
      flags:
      - id: 3
        name: review
        requestee: newreviewer@example.com
        setter: author@example.com
        status: '?'
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Initial commit to review
    blocks: []
    cc:
    - minusreviewer@example.com
    - newreviewer@example.com
    - plusreviewer@example.com
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
    - author: plusreviewer@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review1
      - ''
      - lgtm
    - author: minusreviewer@example.com
      id: 4
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - Bug 1 - Initial commit to review
      - ''
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/2/#review2
      - ''
      - there are problems
    - author: author@example.com
      id: 5
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
