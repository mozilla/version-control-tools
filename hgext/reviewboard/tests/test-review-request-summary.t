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
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/61e2e5c813d2*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:233b570e5356
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
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
    reviewers:
    - reviewer
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: a92d53c0ffc7df0517397a77980e62332552d812
    submitter: default+5
    issue_open_count: 0
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 233b570e5356d0c84bcbf0633de446172012b3b3
    submitter: default+5
    issue_open_count: 0
    status: pending
    reviewers: []

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
    reviewers:
    - reviewer
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: a92d53c0ffc7df0517397a77980e62332552d812
    submitter: default+5
    issue_open_count: 1
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 233b570e5356d0c84bcbf0633de446172012b3b3
    submitter: default+5
    issue_open_count: 0
    status: pending
    reviewers: []

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
    reviewers:
    - reviewer
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: a92d53c0ffc7df0517397a77980e62332552d812
    submitter: default+5
    issue_open_count: 0
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 233b570e5356d0c84bcbf0633de446172012b3b3
    submitter: default+5
    issue_open_count: 0
    status: pending
    reviewers: []

Verify we can also get the summaries by bug, including closed ones.

  $ rbmanage closesubmitted 2

  $ rbmanage dump-summaries-by-bug 1
  - parent:
      summary: bz://1/mynick
      id: 1
      submitter: default+5
      issue_open_count: 0
      status: pending
      reviewers:
      - reviewer
    children:
    - summary: Bug 1 - Foo 1
      id: 2
      commit: a92d53c0ffc7df0517397a77980e62332552d812
      submitter: default+5
      issue_open_count: 0
      status: submitted
      reviewers:
      - reviewer
    - summary: Bug 1 - Foo 2
      id: 3
      commit: 233b570e5356d0c84bcbf0633de446172012b3b3
      submitter: default+5
      issue_open_count: 0
      status: pending
      reviewers: []

Verify that we get nothing from non-existent bugs.

  $ rbmanage dump-summaries-by-bug 2
  []

Cleanup

  $ mozreview stop
  stopped 10 containers
