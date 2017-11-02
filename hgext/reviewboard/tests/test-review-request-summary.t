#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

  $ mozreview create-user reviewer@example.com password1 'Mozilla Reviewer [:reviewer]' --bugzilla-group editbugs
  Created user 6

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/61e2e5c813d2*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:98467d80785e
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:3a446ae43820
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1

  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 1
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 4

Only parents have summaries.

  $ rbmanage dump-summary 2
  API Error: 400: 1001: Review request is not a parent
  [1]

  $ rbmanage create-review 2
  created review 1

Opening an issue should be reflected in the summary.

  $ rbmanage create-diff-comment 2 1 foo 1 'Fix this.' --open-issue
  created diff comment 1
  $ rbmanage publish-review 2 1
  published review 1

  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 1
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 1
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 4

Resolving an issue should decrement the issue count.

  $ rbmanage update-issue-status 2 1 1 resolved
  updated issue status on diff comment 1

  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 1
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 4

Giving a ship-it should result in a change in the reviewer status

  $ exportbzauth reviewer@example.com password1
  $ rbmanage create-review 2 --review-flag='r+' --public
  created review 2

  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 1
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r+
        ship_it: true
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 4

  $ exportbzauth default@example.com password

Verify we can also get the summaries by bug, including closed ones.

  $ rbmanage closesubmitted 2

  $ rbmanage dump-summaries-by-bug 1
  - parent:
      summary: bz://1/mynick
      id: 1
      submitter: default+5
      issue_open_count: 0
      status: pending
      has_draft: false
      reviewers:
      - reviewer
      diff:
        delete: 1
        insert: 1
    children:
    - summary: Bug 1 - Foo 1
      id: 2
      commit: 98467d80785ec84dd871f213c167ed704a6d974d
      submitter: default+5
      issue_open_count: 0
      status: submitted
      has_draft: false
      reviewers:
      - reviewer
      reviewers_status:
        reviewer:
          review_flag: r+
          ship_it: true
      diff:
        delete: 1
        insert: 4
    - summary: Bug 1 - Foo 2
      id: 3
      commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
      submitter: default+5
      issue_open_count: 0
      status: pending
      has_draft: false
      reviewers: []
      reviewers_status: {}
      diff:
        delete: 1
        insert: 4

Verify that we get nothing from non-existent bugs.

  $ rbmanage dump-summaries-by-bug 2
  []

Create a draft with different diffstats

  $ echo "more foo" >> foo
  $ echo "and even more" >> foo
  $ hg commit --amend
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/*.hg (glob)
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:98467d80785e
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:5db0083a9399
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

Verify that requesting the summary as the submitter will show draft diffstats

  $ exportbzauth default@example.com password
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 3
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 0
    status: submitted
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r+
        ship_it: true
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 6

Verify non-submitters will not see the draft diffstats

  $ exportbzauth reviewer@example.com password1
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer
    diff:
      delete: 1
      insert: 1
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 98467d80785ec84dd871f213c167ed704a6d974d
    submitter: default+5
    issue_open_count: 0
    status: submitted
    has_draft: false
    reviewers:
    - reviewer
    reviewers_status:
      reviewer:
        review_flag: r+
        ship_it: true
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 3a446ae4382006c43cdfa5aa33c494f582736f35
    submitter: default+5
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers: []
    reviewers_status: {}
    diff:
      delete: 1
      insert: 4

Cleanup

  $ mozreview stop
  stopped 9 containers
