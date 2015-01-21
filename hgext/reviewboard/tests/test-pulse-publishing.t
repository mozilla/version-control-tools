#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv rb-test-bugzilla

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

Pushing a review should not publish to Pulse

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
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

  $ pulse dump-messages exchange/mozreview/ all
  []

Publishing the review request will send a single message to Pulse with
details from the parent review request

  $ rbmanage publish $HGPORT1 1
TODO this is buggy
  $ pulse dump-messages exchange/mozreview/ all
  []

Cleanup

  $ rbmanage stop ../rbserver

  $ dockercontrol stop-bmo rb-test-bugzilla
  stopped 3 containers
