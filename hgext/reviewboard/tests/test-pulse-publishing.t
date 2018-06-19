#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-bugzilla

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

  $ mozreview create-user reviewer1@example.com r1password 'Mozilla Reviewer [:reviewer1]' --bugzilla-group editbugs
  Created user 6
  $ mozreview create-user reviewer2@example.com r2password 'Mozilla Reviewer2 [:reviewer2]' --bugzilla-group editbugs
  Created user 7

Pushing a review should not publish to Pulse

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

  $ pulse dump-messages exchange/mozreview/ all
  []

Publishing the review request will send a single message to Pulse with
details from the parent review request

  $ rbmanage publish 1
  $ pulse dump-messages exchange/mozreview/ all
  - _meta:
      exchange: exchange/mozreview/
      routing_key: mozreview.commits.published
    commits:
    - diffset_revision: 1
      rev: 98467d80785ec84dd871f213c167ed704a6d974d
      review_request_id: 2
    - diffset_revision: 1
      rev: 3a446ae4382006c43cdfa5aa33c494f582736f35
      review_request_id: 3
    landing_repository_url: null
    parent_diffset_revision: 1
    parent_review_request_id: 1
    repository_url: http://$DOCKER_HOSTNAME:$HGPORT/test-repo
    review_board_url: http://$DOCKER_HOSTNAME:$HGPORT1/

Creating a review will send a Pulse message

  $ exportbzauth reviewer1@example.com r1password
  $ rbmanage create-review 2 --body-top LGTM --public --review-flag='r+'
  created review 1

  $ pulse dump-messages exchange/mozreview/ all
  - _meta:
      exchange: exchange/mozreview/
      routing_key: mozreview.review.published
    repository_bugtracker_url: http://$DOCKER_HOSTNAME:$HGPORT2/show_bug.cgi?id=%s
    repository_id: 1
    repository_url: http://$DOCKER_HOSTNAME:$HGPORT/test-repo
    review_board_url: http://$DOCKER_HOSTNAME:$HGPORT1/
    review_id: 1
    review_request_bugs:
    - '1'
    review_request_id: 2
    review_request_participants:
    - reviewer1
    review_request_submitter: default+5
    review_request_target_people: []
    review_time: \d+ (re)
    review_username: reviewer1

Creating a reply will send a Pulse message

  $ exportbzauth reviewer2@example.com r2password
  $ rbmanage create-review-reply 2 1 --body-bottom 'I agree' --public
  created review reply 2

  $ pulse dump-messages exchange/mozreview/ all
  - _meta:
      exchange: exchange/mozreview/
      routing_key: mozreview.review.published
    repository_bugtracker_url: http://$DOCKER_HOSTNAME:$HGPORT2/show_bug.cgi?id=%s
    repository_id: 1
    repository_url: http://$DOCKER_HOSTNAME:$HGPORT/test-repo
    review_board_url: http://$DOCKER_HOSTNAME:$HGPORT1/
    review_id: 2
    review_request_bugs:
    - '1'
    review_request_id: 2
    review_request_participants:
    - reviewer1
    - reviewer2
    review_request_submitter: default+5
    review_request_target_people: []
    review_time: \d+ (re)
    review_username: reviewer2

Cleanup

  $ mozreview stop
  stopped 7 containers
