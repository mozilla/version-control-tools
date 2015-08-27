#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Create both an l3 and l1 user so we can test approval in each case

  $ mozreview create-user l3@example.com password 'L3 Contributor [:level3]'  --uid 2002 --scm-level 3 --bugzilla-group editbugs
  Created user 6
  $ l3apikey=`mozreview create-api-key l3@example.com`
  $ exportbzauth l3@example.com password
We dump l3 using the l3 user so that it's imported into the RB database
  $ rbmanage dump-user level3 > /dev/null
  $ rbmanage associate-ldap-user level3 l3@example.com
  l3@example.com associated with level3
  $ mozreview create-user l1a@example.com password 'L1 ContributorA [:level1a]'  --uid 2003 --scm-level 1
  Created user 7
  $ l1aapikey=`mozreview create-api-key l1a@example.com`
  $ mozreview create-user l1b@example.com password 'L1 ContributorB [:level1b]'  --uid 2004 --scm-level 1
  Created user 8

  $ exportbzauth l1a@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ bugzilla create-bug TestProduct TestComponent 'Second Bug'

Create a review request from an L1 user

  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ export SSH_KEYNAME=l1a@example.com
  $ hg --config bugzilla.username=l1a@example.com --config bugzilla.apikey=${l1aapikey} push > /dev/null
  $ rbmanage add-reviewer 2 --user level3
  1 people listed on review request
  $ rbmanage add-reviewer 2 --user level1b
  2 people listed on review request
  $ rbmanage publish 1
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Have an L1 user provide a ship it review which should not grant approval

  $ exportbzauth l1b@example.com password
  $ rbmanage create-review 2 --body-top "Ship-it!" --public --ship-it
  created review 1
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []

Have an L3 user provide a ship it review which should grant approval

  $ exportbzauth l3@example.com password
  $ rbmanage create-review 2 --body-top "Ship-it!" --public --ship-it
  created review 2
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 2
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []

Posting a new review without ship it should cancel the previous approval
  $ rbmanage create-review 2 --body-top "Don't Land it!" --public
  created review 3
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 3
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []

One more ship it should switch it back to approved

  $ rbmanage create-review 2 --body-top "NVM, Ship-it!" --public --ship-it
  created review 4
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 4
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []
  - id: 4
    public: true
    ship_it: true
    body_top: NVM, Ship-it!
    body_top_text_type: plain
    diff_comments: []

Since the author is L1, adding a new diff should cancel approval

  $ echo modified > foo
  $ hg commit --amend > /dev/null
  $ export SSH_KEYNAME=l1a@example.com
  $ hg --config bugzilla.username=l1a@example.com --config bugzilla.apikey=${l1aapikey} push > /dev/null
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 473206d1f704058758360f38c6fbf9c557bac746
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 4
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []
  - id: 4
    public: true
    ship_it: true
    body_top: NVM, Ship-it!
    body_top_text_type: plain
    diff_comments: []

A new ship-it from L3 should give approval

  $ rbmanage create-review 2 --body-top "Update looks good!" --public --ship-it
  created review 5
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 473206d1f704058758360f38c6fbf9c557bac746
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 5
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []
  - id: 4
    public: true
    ship_it: true
    body_top: NVM, Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 5
    public: true
    ship_it: true
    body_top: Update looks good!
    body_top_text_type: plain
    diff_comments: []

Opening issues, even from an L1 user, should revoke approval until they're fixed

  $ exportbzauth l1b@example.com password
  $ rbmanage create-review 2 --body-top "I found issues"
  created review 6
  $ rbmanage create-diff-comment 2 6 foo 1 "Issue Text" --open-issue
  created diff comment 1
  $ rbmanage publish-review 2 6
  published review 6
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 473206d1f704058758360f38c6fbf9c557bac746
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: The review request has open issues.
  review_count: 6
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []
  - id: 4
    public: true
    ship_it: true
    body_top: NVM, Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 5
    public: true
    ship_it: true
    body_top: Update looks good!
    body_top_text_type: plain
    diff_comments: []
  - id: 6
    public: true
    ship_it: false
    body_top: I found issues
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: level1b
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: Issue Text
      text_type: plain
      diff_id: 4
      diff_dest_file: foo
    diff_count: 1

Fixing the issue should restore approval

  $ rbmanage update-issue-status 2 6 1 resolved
  updated issue status on diff comment 1
  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: level1a
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people:
  - level1b
  - level3
  extra_data:
    p2rb: true
    p2rb.commit_id: 473206d1f704058758360f38c6fbf9c557bac746
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 6
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 2
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 3
    public: true
    ship_it: false
    body_top: Don't Land it!
    body_top_text_type: plain
    diff_comments: []
  - id: 4
    public: true
    ship_it: true
    body_top: NVM, Ship-it!
    body_top_text_type: plain
    diff_comments: []
  - id: 5
    public: true
    ship_it: true
    body_top: Update looks good!
    body_top_text_type: plain
    diff_comments: []
  - id: 6
    public: true
    ship_it: false
    body_top: I found issues
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: level1b
      issue_opened: true
      issue_status: resolved
      first_line: 1
      num_lines: 1
      text: Issue Text
      text_type: plain
      diff_id: 4
      diff_dest_file: foo
    diff_count: 1

Review requests created by L3 users

  $ exportbzauth l3@example.com password
  $ echo author2 > foo
  $ hg commit --amend -m "Bug 2 - initial commit to review" > /dev/null
  $ export SSH_KEYNAME=l3@example.com
  $ hg --config bugzilla.username=l3@example.com --config bugzilla.apikey=${l3apikey} push > /dev/null
  $ rbmanage add-reviewer 4 --user level1a
  1 people listed on review request
  $ rbmanage add-reviewer 4 --user level1b
  2 people listed on review request
  $ rbmanage publish 3
  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: true
  bugs:
  - '2'
  commit: null
  submitter: level3
  summary: Bug 2 - initial commit to review
  description: Bug 2 - initial commit to review
  target_people:
  - level1a
  - level1b
  extra_data:
    p2rb: true
    p2rb.commit_id: c1ebcda638274d5217801b7f05e33b848ff39be1
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Even a ship-it from an L1 user will give approval to an L3 author

  $ exportbzauth l1a@example.com password
  $ rbmanage create-review 4 --body-top "Ship-it!" --public --ship-it
  created review 7
  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: true
  bugs:
  - '2'
  commit: null
  submitter: level3
  summary: Bug 2 - initial commit to review
  description: Bug 2 - initial commit to review
  target_people:
  - level1a
  - level1b
  extra_data:
    p2rb: true
    p2rb.commit_id: c1ebcda638274d5217801b7f05e33b848ff39be1
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 1
  reviews:
  - id: 7
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []

We trust L3 authors to update diffs and carry forward approval from previous
ship-its. Posting a new diff should not clear approval

  $ exportbzauth l3@example.com password
  $ echo modified2 > foo
  $ hg commit --amend > /dev/null
  $ export SSH_KEYNAME=l3@example.com
  $ hg --config bugzilla.username=l3@example.com --config bugzilla.apikey=${l3apikey} push > /dev/null
  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: true
  bugs:
  - '2'
  commit: null
  submitter: level3
  summary: Bug 2 - initial commit to review
  description: Bug 2 - initial commit to review
  target_people:
  - level1a
  - level1b
  extra_data:
    p2rb: true
    p2rb.commit_id: bccc4c4e590eeefbb42491f1bb061143a49bdaf8
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  approved: true
  approval_failure: null
  review_count: 1
  reviews:
  - id: 7
    public: true
    ship_it: true
    body_top: Ship-it!
    body_top_text_type: plain
    diff_comments: []

  $ cd ..

Cleanup

  $ mozreview stop
  stopped 9 containers
