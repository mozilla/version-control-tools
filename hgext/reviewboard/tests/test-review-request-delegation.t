#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo0 > foo
  $ hg -q commit -A -m 'root commit'
  $ hg phase --public -r .

Set up users

  $ mozreview create-user l3author@example.com password 'L3 Contributor [:l3author]' --scm-level 3 --uid 2004 --key-file "$MOZREVIEW_HOME/keys/l3author@example.com"
  Created user 6
  $ mozreview create-user reviewer1@example.com password 'Reviewer 1 [:reviewer1]' --scm-level 3  --bugzilla-group editbugs --uid 2005 --key-file "$MOZREVIEW_HOME/keys/reviewer1@example.com"
  Created user 7
  $ mozreview create-user reviewer2@example.com password 'Reviewer 2 [:reviewer2]' --scm-level 3 --uid 2006 --key-file "$MOZREVIEW_HOME/keys/reviewer2@example.com"
  Created user 8

Create bug and review

  $ l3key=`mozreview create-api-key l3author@example.com`
  $ exportbzauth l3author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo fruit > foo
  $ hg commit -m 'Bug 1 - Initial commit to review r?reviewer1'
  $ echo water >> foo
  $ hg commit -m 'Bug 1 - Forgot water r?reviewer1'
  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=$l3key --config reviewboard.autopublish=true push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:80ffd9136b8b
  summary:    Bug 1 - Initial commit to review r?reviewer1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:493559840037
  summary:    Bug 1 - Forgot water r?reviewer1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (published review request 1)

Change the reviewer while logged in as reviewer1

  $ exportbzauth reviewer1@example.com password
  $ rbmanage modify-reviewers 1 2 'reviewer2'
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer2
    reviewers_status:
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4

Test multiple reviewers

  $ rbmanage modify-reviewers 1 2 'reviewer1,reviewer2'
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4

Test invalid reviewer

  $ rbmanage modify-reviewers 1 2 'invalid'
  API Error: 400: 105: The reviewer 'invalid' was not found
  [1]

Change the reviewer while logged in as the submitter

  $ exportbzauth l3author@example.com password
  $ rbmanage modify-reviewers 1 2 'reviewer2'
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer2
    reviewers_status:
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4

Test user without editbugs

  $ exportbzauth reviewer2@example.com password
  $ rbmanage modify-reviewers 1 2 'reviewer1'
  API Error: 500: 225: Error publishing: Bugzilla error: You are not authorized to edit attachment 1.
  [1]

Test verify-reviewers

  $ rbmanage verify-reviewers 'reviewer1'
  $ rbmanage verify-reviewers 'reviewer1,reviewer2'
  $ rbmanage verify-reviewers 'invalid'
  API Error: 400: 105: The reviewer 'invalid' was not found
  [1]
  $ rbmanage verify-reviewers 'reviewer1,invalid'
  API Error: 400: 105: The reviewer 'invalid' was not found
  [1]

Test ensure-drafts

  $ exportbzauth l3author@example.com password
  $ rbmanage add-reviewer 2 --user reviewer1
  2 people listed on review request
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer2
    reviewers_status:
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4
  $ rbmanage ensure-drafts 1
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer2
    reviewers_status:
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: true
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4
  $ rbmanage publish 1
  $ rbmanage dump-summary 1
  parent:
    summary: bz://1/mynick
    id: 1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    diff:
      delete: 1
      insert: 2
  children:
  - summary: Bug 1 - Initial commit to review r?reviewer1
    id: 2
    commit: 80ffd9136b8b9d9541de1780e1a3e027665017fb
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    - reviewer2
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
      reviewer2:
        review_flag: r?
        ship_it: false
    diff:
      delete: 1
      insert: 4
  - summary: Bug 1 - Forgot water r?reviewer1
    id: 3
    commit: 4935598400374354824ffde84a8b6767823100d1
    submitter: l3author
    issue_open_count: 0
    status: pending
    has_draft: false
    reviewers:
    - reviewer1
    reviewers_status:
      reviewer1:
        review_flag: r?
        ship_it: false
    diff:
      delete: 0
      insert: 4
