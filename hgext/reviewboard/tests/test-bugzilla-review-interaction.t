#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ mozreview create-user author@example.com password 'Some Contributor' --uid 2001 --scm-level 1
  Created user 6
  $ authorkey=`mozreview create-api-key author@example.com`
  $ alias hgauthor='hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey}'
  $ mozreview create-user reviewer@example.com password 'Mozilla Reviewer [:reviewer]' --bugzilla-group editbugs
  Created user 7
  $ mozreview create-user reviewer2@example.com password 'Another Reviewer [:rev2]' --bugzilla-group editbugs
  Created user 8
  $ mozreview create-user troll@example.com password 'Reviewer Troll [:troll]' --bugzilla-group editbugs
  Created user 9

Create a review request from a regular user

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hgauthor push > /dev/null

Adding a reviewer should result in a r? flag being set

  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/diff/#index_header (glob)
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
      - 'Review commit: http://*:$HGPORT1/r/2/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/2/' (glob)
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Adding a "Ship It" review will grant r+

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 2 --body-top LGTM --public --ship-it
  created review 1

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/diff/#index_header (glob)
      description: 'MozReview Request: Bug 1 - Initial commit to review'
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
      - 'Review commit: http://*:$HGPORT1/r/2/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/2/' (glob)
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://*:$HGPORT1/r/2/#review1 (glob)
      - ''
      - LGTM
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Adding a reply to the review will add a comment to Bugzilla

  $ exportbzauth author@example.com password
  $ rbmanage create-review-reply 2 1 --body-bottom 'Thanks!' --public
  created review reply 2

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/2/diff/#index_header (glob)
      description: 'MozReview Request: Bug 1 - Initial commit to review'
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
      - 'Review commit: http://*:$HGPORT1/r/2/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/2/' (glob)
    - author: reviewer@example.com
      id: 3
      tags: []
      text:
      - Comment on attachment 1
      - 'MozReview Request: Bug 1 - Initial commit to review'
      - ''
      - http://*:$HGPORT1/r/2/#review1 (glob)
      - ''
      - LGTM
    - author: author@example.com
      id: 4
      tags: []
      text:
      - http://*:$HGPORT1/r/2/#review1 (glob)
      - ''
      - Thanks!
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Ensure multiple reviewers works as expected

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Multiple Reviewers'

  $ hg -q up -r 0
  $ echo b2 > foo
  $ hg commit -m 'Bug 2 - Multiple reviewers'
  created new head
  $ hgauthor push > /dev/null

Emulate the JavaScript by setting the reviewers on both parent and commit.
TODO: Implement the JavaScript bits on the server so we don't need to do this
in the tests.

  $ rbmanage add-reviewer 3 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage add-reviewer 4 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage publish 3

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/4/diff/#index_header (glob)
      description: 'MozReview Request: Bug 2 - Multiple reviewers'
      file_name: reviewboard-4-url.txt
      flags:
      - id: 2
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 3
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Multiple reviewers'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 5
      tags: []
      text: ''
    - author: author@example.com
      id: 6
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/4/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/4/' (glob)
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Multiple Reviewers

Removing a reviewer should remove their review flag

  $ rbmanage remove-reviewer 3 --user rev2
  1 people listed on review request
  $ rbmanage remove-reviewer 4 --user rev2
  1 people listed on review request

  $ rbmanage publish 3

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/4/diff/#index_header (glob)
      description: 'MozReview Request: Bug 2 - Multiple reviewers'
      file_name: reviewboard-4-url.txt
      flags:
      - id: 3
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Multiple reviewers'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 5
      tags: []
      text: ''
    - author: author@example.com
      id: 6
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/4/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/4/' (glob)
    - author: author@example.com
      id: 7
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review request updated; see interdiff: http://*/r/4/diff/1-2/' (glob)
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Multiple Reviewers

Removing all reviewers should remove all flags

  $ rbmanage remove-reviewer 3 --user reviewer
  0 people listed on review request
  $ rbmanage remove-reviewer 4 --user reviewer
  0 people listed on review request

  $ rbmanage publish 3

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/4/diff/#index_header (glob)
      description: 'MozReview Request: Bug 2 - Multiple reviewers'
      file_name: reviewboard-4-url.txt
      flags: []
      id: 2
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 2 - Multiple reviewers'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 5
      tags: []
      text: ''
    - author: author@example.com
      id: 6
      tags: []
      text:
      - Created attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/4/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/4/' (glob)
    - author: author@example.com
      id: 7
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review request updated; see interdiff: http://*/r/4/diff/1-2/' (glob)
    - author: author@example.com
      id: 8
      tags: []
      text:
      - Comment on attachment 2
      - 'MozReview Request: Bug 2 - Multiple reviewers'
      - ''
      - 'Review request updated; see interdiff: http://*/r/4/diff/1-2/' (glob)
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Multiple Reviewers

review? sticks around when 1 person grants review

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'More Multiple Reviewers'

  $ hg -q up -r 0
  $ echo more_multiple_reviewers > foo
  $ hg commit -m 'Bug 3 - More multiple reviewers'
  created new head
  $ hgauthor push > /dev/null

  $ rbmanage add-reviewer 5 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage add-reviewer 6 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage publish 5

  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 6 --body-top 'land it!' --public --ship-it
  created review 3

  $ bugzilla dump-bug 3
  Bug 3:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/6/diff/#index_header (glob)
      description: 'MozReview Request: Bug 3 - More multiple reviewers'
      file_name: reviewboard-6-url.txt
      flags:
      - id: 4
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 5
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 3
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 3 - More multiple reviewers'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 9
      tags: []
      text: ''
    - author: author@example.com
      id: 10
      tags: []
      text:
      - Created attachment 3
      - 'MozReview Request: Bug 3 - More multiple reviewers'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/6/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/6/' (glob)
    - author: reviewer@example.com
      id: 11
      tags: []
      text:
      - Comment on attachment 3
      - 'MozReview Request: Bug 3 - More multiple reviewers'
      - ''
      - http://*:$HGPORT1/r/6/#review3 (glob)
      - ''
      - land it!
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: More Multiple Reviewers

Random users can come along and grant review

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Unrelated Reviewers'

  $ hg -q up -r 0
  $ echo unrelated_reviewer > foo
  $ hg commit -m 'Bug 4 - Unrelated Reviewers'
  created new head
  $ hgauthor push > /dev/null

  $ rbmanage add-reviewer 7 --user reviewer
  1 people listed on review request
  $ rbmanage add-reviewer 8 --user reviewer
  1 people listed on review request
  $ rbmanage publish 7

  $ exportbzauth troll@example.com password
  $ rbmanage create-review 8 --body-top 'I am always watching' --public --ship-it
  created review 4

  $ bugzilla dump-bug 4
  Bug 4:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/8/diff/#index_header (glob)
      description: 'MozReview Request: Bug 4 - Unrelated Reviewers'
      file_name: reviewboard-8-url.txt
      flags:
      - id: 6
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      - id: 7
        name: review
        requestee: null
        setter: troll@example.com
        status: +
      id: 4
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 4 - Unrelated Reviewers'
    blocks: []
    cc:
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 12
      tags: []
      text: ''
    - author: author@example.com
      id: 13
      tags: []
      text:
      - Created attachment 4
      - 'MozReview Request: Bug 4 - Unrelated Reviewers'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/8/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/8/' (glob)
    - author: troll@example.com
      id: 14
      tags: []
      text:
      - Comment on attachment 4
      - 'MozReview Request: Bug 4 - Unrelated Reviewers'
      - ''
      - http://*:$HGPORT1/r/8/#review4 (glob)
      - ''
      - I am always watching
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Unrelated Reviewers

Test interaction with multiple commits.

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Parent Reviews'

  $ hg -q up -r 0
  $ echo parent_reviews > foo
  $ hg commit -m 'Bug 5 - Parent reviews'
  created new head
  $ echo parent_reviews_2 >> foo
  $ hg commit -m 'Bug 5 - Parent reviews, second commit'
  $ echo parent_reviews_3 >> foo
  $ hg commit -m 'Bug 5 - Parent reviews, third commit'
  $ hgauthor push > /dev/null

  $ rbmanage add-reviewer 9 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage add-reviewer 10 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage add-reviewer 11 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage add-reviewer 12 --user reviewer --user rev2
  2 people listed on review request
  $ rbmanage publish 9

  $ bugzilla dump-bug 5
  Bug 5:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/10/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews'
      file_name: reviewboard-10-url.txt
      flags:
      - id: 8
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 9
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/11/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, second commit'
      file_name: reviewboard-11-url.txt
      flags:
      - id: 10
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 11
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 6
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, second commit'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/12/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, third commit'
      file_name: reviewboard-12-url.txt
      flags:
      - id: 12
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 13
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 7
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, third commit'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 15
      tags: []
      text: ''
    - author: author@example.com
      id: 16
      tags: []
      text:
      - Created attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/10/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/10/' (glob)
    - author: author@example.com
      id: 17
      tags: []
      text:
      - Created attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/11/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/11/' (glob)
    - author: author@example.com
      id: 18
      tags: []
      text:
      - Created attachment 7
      - 'MozReview Request: Bug 5 - Parent reviews, third commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/12/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/12/' (glob)
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Parent Reviews

  $ exportbzauth reviewer@example.com password

Verify that a single ship-it r+s only that attachment.

  $ rbmanage create-review 11 --body-top 'land it!' --public --ship-it
  created review 5

  $ bugzilla dump-bug 5
  Bug 5:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/10/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews'
      file_name: reviewboard-10-url.txt
      flags:
      - id: 8
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 9
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/11/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, second commit'
      file_name: reviewboard-11-url.txt
      flags:
      - id: 10
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 11
        name: review
        requestee: null
        setter: reviewer@example.com
        status: +
      id: 6
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, second commit'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/12/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, third commit'
      file_name: reviewboard-12-url.txt
      flags:
      - id: 12
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 13
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 7
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, third commit'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 15
      tags: []
      text: ''
    - author: author@example.com
      id: 16
      tags: []
      text:
      - Created attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/10/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/10/' (glob)
    - author: author@example.com
      id: 17
      tags: []
      text:
      - Created attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/11/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/11/' (glob)
    - author: author@example.com
      id: 18
      tags: []
      text:
      - Created attachment 7
      - 'MozReview Request: Bug 5 - Parent reviews, third commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/12/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/12/' (glob)
    - author: reviewer@example.com
      id: 19
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review5 (glob)
      - ''
      - land it!
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Parent Reviews

Ship-it reviews are not allowed on the parent.

  $ rbmanage create-review 9 --body-top 'all good!' --public --ship-it
  API Error: 500: 225: Error publishing: "Ship it" reviews on parent review requests are not allowed.  Please review individual commits.
  [1]

A non-ship-it review on a child should clear only that attachment's r+.

  $ rbmanage create-review 11 --body-top 'there is a problem' --public
  created review 7

  $ bugzilla dump-bug 5
  Bug 5:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/10/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews'
      file_name: reviewboard-10-url.txt
      flags:
      - id: 8
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 9
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/11/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, second commit'
      file_name: reviewboard-11-url.txt
      flags:
      - id: 10
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      id: 6
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, second commit'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/12/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, third commit'
      file_name: reviewboard-12-url.txt
      flags:
      - id: 12
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 13
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 7
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, third commit'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 15
      tags: []
      text: ''
    - author: author@example.com
      id: 16
      tags: []
      text:
      - Created attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/10/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/10/' (glob)
    - author: author@example.com
      id: 17
      tags: []
      text:
      - Created attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/11/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/11/' (glob)
    - author: author@example.com
      id: 18
      tags: []
      text:
      - Created attachment 7
      - 'MozReview Request: Bug 5 - Parent reviews, third commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/12/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/12/' (glob)
    - author: reviewer@example.com
      id: 19
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review5 (glob)
      - ''
      - land it!
    - author: reviewer@example.com
      id: 20
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review7 (glob)
      - ''
      - there is a problem
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Parent Reviews

A non-ship-it review on a child should also clear the attachment's r?.

  $ exportbzauth reviewer2@example.com password
  $ rbmanage create-review 10 --body-top 'this is not good' --public
  created review 8

  $ bugzilla dump-bug 5
  Bug 5:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/10/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews'
      file_name: reviewboard-10-url.txt
      flags:
      - id: 9
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/11/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, second commit'
      file_name: reviewboard-11-url.txt
      flags:
      - id: 10
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      id: 6
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, second commit'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/12/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, third commit'
      file_name: reviewboard-12-url.txt
      flags:
      - id: 12
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 13
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 7
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, third commit'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 15
      tags: []
      text: ''
    - author: author@example.com
      id: 16
      tags: []
      text:
      - Created attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/10/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/10/' (glob)
    - author: author@example.com
      id: 17
      tags: []
      text:
      - Created attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/11/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/11/' (glob)
    - author: author@example.com
      id: 18
      tags: []
      text:
      - Created attachment 7
      - 'MozReview Request: Bug 5 - Parent reviews, third commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/12/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/12/' (glob)
    - author: reviewer@example.com
      id: 19
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review5 (glob)
      - ''
      - land it!
    - author: reviewer@example.com
      id: 20
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review7 (glob)
      - ''
      - there is a problem
    - author: reviewer2@example.com
      id: 21
      tags: []
      text:
      - Comment on attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - http://*:$HGPORT1/r/10/#review8 (glob)
      - ''
      - this is not good
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Parent Reviews

A non-ship-it review on a parent should post a comment only.

  $ exportbzauth reviewer2@example.com password
  $ rbmanage create-review 9 --body-top 'actually none of this is good' --public
  created review 9

  $ bugzilla dump-bug 5
  Bug 5:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/10/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews'
      file_name: reviewboard-10-url.txt
      flags:
      - id: 9
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/11/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, second commit'
      file_name: reviewboard-11-url.txt
      flags:
      - id: 10
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      id: 6
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, second commit'
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://*:$HGPORT1/r/12/diff/#index_header (glob)
      description: 'MozReview Request: Bug 5 - Parent reviews, third commit'
      file_name: reviewboard-12-url.txt
      flags:
      - id: 12
        name: review
        requestee: reviewer2@example.com
        setter: author@example.com
        status: '?'
      - id: 13
        name: review
        requestee: reviewer@example.com
        setter: author@example.com
        status: '?'
      id: 7
      is_obsolete: false
      is_patch: false
      summary: 'MozReview Request: Bug 5 - Parent reviews, third commit'
    blocks: []
    cc:
    - reviewer2@example.com
    - reviewer@example.com
    comments:
    - author: author@example.com
      id: 15
      tags: []
      text: ''
    - author: author@example.com
      id: 16
      tags: []
      text:
      - Created attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/10/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/10/' (glob)
    - author: author@example.com
      id: 17
      tags: []
      text:
      - Created attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/11/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/11/' (glob)
    - author: author@example.com
      id: 18
      tags: []
      text:
      - Created attachment 7
      - 'MozReview Request: Bug 5 - Parent reviews, third commit'
      - ''
      - 'Review commit: http://*:$HGPORT1/r/12/diff/#index_header' (glob)
      - 'See other reviews: http://*:$HGPORT1/r/12/' (glob)
    - author: reviewer@example.com
      id: 19
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review5 (glob)
      - ''
      - land it!
    - author: reviewer@example.com
      id: 20
      tags: []
      text:
      - Comment on attachment 6
      - 'MozReview Request: Bug 5 - Parent reviews, second commit'
      - ''
      - http://*:$HGPORT1/r/11/#review7 (glob)
      - ''
      - there is a problem
    - author: reviewer2@example.com
      id: 21
      tags: []
      text:
      - Comment on attachment 5
      - 'MozReview Request: Bug 5 - Parent reviews'
      - ''
      - http://*:$HGPORT1/r/10/#review8 (glob)
      - ''
      - this is not good
    - author: reviewer2@example.com
      id: 22
      tags: []
      text:
      - http://*:$HGPORT1/r/9/#review9 (glob)
      - ''
      - actually none of this is good
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: Parent Reviews

  $ cd ..

Cleanup

  $ mozreview stop
  stopped 10 containers
