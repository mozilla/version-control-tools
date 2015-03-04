#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

  $ bugzilla create-user reviewer@example.com password1 'Mozilla Reviewer [:reviewer]' --group editbugs
  created user 5

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 2 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ rbmanage add-reviewer $HGPORT1 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish $HGPORT1 1

  $ rbmanage dump-summary $HGPORT1 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []

Only parents have summaries.

  $ rbmanage dump-summary $HGPORT1 2
  API Error: 400: 1001: Review request is not a parent
  [1]

  $ rbmanage create-review $HGPORT1 2
  created review 1

Opening an issue should be reflected in the summary.

  $ rbmanage create-diff-comment $HGPORT1 2 1 foo 1 'Fix this.' --open-issue
  created diff comment 1
  $ rbmanage publish-review $HGPORT1 2 1
  published review 1

  $ rbmanage dump-summary $HGPORT1 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    submitter: admin+1
    issue_open_count: 1
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []

Resolving an issue should decrement the issue count.

  $ rbmanage update-issue-status $HGPORT1 2 1 1 resolved
  updated issue status on diff comment 1

  $ rbmanage dump-summary $HGPORT1 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []
  children:
  - summary: Bug 1 - Foo 1
    id: 2
    commit: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers:
    - reviewer
  - summary: Bug 1 - Foo 2
    id: 3
    commit: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    submitter: admin+1
    issue_open_count: 0
    status: pending
    reviewers: []

Cleanup

  $ mozreview stop
  stopped 5 containers
