#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo0 > foo
  $ hg -q commit -A -m 'root commit'
  $ hg phase --public -r .

Set up users

  $ mozreview create-user reviewer@example.com password 'Reviewer [:reviewer]' --scm-level 3 --bugzilla-group editbugs
  Created user 6
  $ mozreview create-user l3author@example.com password 'L3 Contributor [:l3author]' --scm-level 3 --uid 2004 --key-file "$MOZREVIEW_HOME/keys/l3author@example.com"
  Created user 7
  $ l3key=`mozreview create-api-key l3author@example.com`
  $ exportbzauth l3author@example.com password

Create bug and review

  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo bug > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=$l3key --config reviewboard.autopublish=true push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:63c61970184b
  summary:    Bug 1 - Initial commit to review
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)? y
  (published review request 1)
  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1
  $ rbmanage dump-rewrite-commit 1
  API Error: 405: 1008: Unable to continue as the review has not been approved.
  [1]
  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 2 --body-top "Ship-it!" --public --ship-it
  created review 1

Check for rewrite on parent

  $ rbmanage dump-rewrite-commit 1
  commits:
  - commit: 63c61970184bac9e9ae1660344e26e98587b0103
    id: 2
    reviewers:
    - reviewer
    summary:
    - Bug 1 - Initial commit to review r=reviewer
    - ''
    - 'MozReview-Commit-ID: 124Bxg'

Rewriting on a child should work against the parent

  $ rbmanage dump-rewrite-commit 2
  commits:
  - commit: 63c61970184bac9e9ae1660344e26e98587b0103
    id: 2
    reviewers:
    - reviewer
    summary:
    - Bug 1 - Initial commit to review r=reviewer
    - ''
    - 'MozReview-Commit-ID: 124Bxg'

  $ mozreview stop
  stopped 9 containers
