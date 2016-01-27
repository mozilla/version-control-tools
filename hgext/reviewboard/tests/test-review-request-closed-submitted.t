#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ bugzilla create-bug TestProduct TestComponent summary

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
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

  $ rbmanage publish 1

Close the squashed review request as submitted, which should close all of the
child review requests.

  $ rbmanage closesubmitted 1

Squashed review request with ID 1 should be closed as submitted...

  $ rbmanage dumpreview 1
  id: 1
  status: submitted
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.base_commit: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo0
    - +foo2
    - ''
  approved: false
  approval_failure: Commit a92d53c0ffc7df0517397a77980e62332552d812 is not approved.

Child review request with ID 2 should be closed as submitted...

  $ rbmanage dumpreview 2
  id: 2
  status: submitted
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 2
    revision: 1
    base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo0
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

  $ rbmanage dumpreview 3
  id: 3
  status: submitted
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo1
    - +foo2
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Submitting against a published review request results in error
TODO Fix the error output (bug 1169664)

  $ echo foo3 > foo
  $ hg commit -m 'Bug 1 - Foo 3'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 3 changesets for review
  abort: reviewboard error: "HTTP 500". please try submitting the review again. if that doesn't work, you've likely encountered a bug.
  [255]

Re-opening the parent review request should re-open all of the children.

  $ rbmanage reopen 1

Squashed review request with ID 1 should be re-opened...

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.base_commit: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo0
    - +foo2
    - ''
  approved: false
  approval_failure: Commit a92d53c0ffc7df0517397a77980e62332552d812 is not approved.

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 2
    revision: 1
    base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo0
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview 3
  id: 3
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 233b570e5356d0c84bcbf0633de446172012b3b3
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: a92d53c0ffc7df0517397a77980e62332552d812
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo1
    - +foo2
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Cleanup

  $ mozreview stop
  stopped 10 containers
