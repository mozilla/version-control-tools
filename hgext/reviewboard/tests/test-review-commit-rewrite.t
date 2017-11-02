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
  $ hg --config bugzilla.username=l3author@example.com --config bugzilla.apikey=$l3key push
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
  
  publish these review requests now (Yn)?  y
  (published review request 1)
  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request
  $ rbmanage publish 1
  $ rbmanage dump-rewrite-commit 1
  API Error: 405: 1008: Unable to continue as the review has not been approved.
  [1]
  $ exportbzauth reviewer@example.com password
  $ rbmanage create-review 2 --body-top "Ship-it!" --public --review-flag='r+'
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

Check rewriting when submitter == reviewer

  $ bugzilla create-bug TestProduct TestComponent 'Second Bug'
  $ echo another >> foo
  $ hg commit -m 'Bug 2 - Initial commit to review r?l3author' foo
  $ exportbzauth l3author@example.com password
  $ hg --verbose --config bugzilla.username=l3author@example.com --config bugzilla.apikey=$l3key push -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  committing files:
  foo
  committing manifest
  committing changelog
  resolving manifests
  1 changesets found
  uncompressed size of bundle content:
       218 (changelog)
       165 (manifests)
       135  foo
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/ee66baf1dbbf-77ce5791-addcommitid.hg (glob)
  1 changesets found
  uncompressed size of bundle content:
       247 (changelog)
       165 (manifests)
       135  foo
  adding branch
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  searching for changes
  1 changesets found
  uncompressed size of bundle content:
       247 (changelog)
       165 (manifests)
       135  foo
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  2:ec1c2da051b2
  summary:    Bug 2 - Initial commit to review r?l3author
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 3)
  $ rbmanage create-review 4 --body-top "Ship-it!" --public --review-flag='r+'
  created review 2
  $ rbmanage dump-rewrite-commit 3
  commits:
  - commit: ec1c2da051b299ce4473a30fad8c7affddc68d14
    id: 4
    reviewers:
    - l3author
    summary:
    - Bug 2 - Initial commit to review r=l3author
    - ''
    - 'MozReview-Commit-ID: 5ijR9k'

  $ mozreview stop
  stopped 9 containers
