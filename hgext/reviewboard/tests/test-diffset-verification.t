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
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/24417bc94b2c*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:98467d80785e
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage add-reviewer 2 --user reviewer
  1 people listed on review request

Manually upload a diff replacing the one present on the draft so that
the review requests DiffSet isn't verified.

  $ hg update .~1 > /dev/null
  $ echo bar > foo
  $ hg commit -m 'Bug 1 - Bar' > /dev/null
  $ hg export | rbmanage upload-diff 1 --base-commit `hg log -r .~1 --template '{node}'`

Attempting to publish the manually uploaded diff should fail because it
is not verified.

  $ rbmanage publish 1
  API Error: 500: 225: Error publishing: This review request draft contained a manually uploaded diff, which is prohibited. Please push to the review server to create review requests. If you believe you received this message in error, please file a bug.
  [1]

Cleanup

  $ mozreview stop
  stopped 9 containers
