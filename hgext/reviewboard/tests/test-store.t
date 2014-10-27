#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-store

  $ bugzilla create-bug TestProduct TestComponent 1

Pushing a review will create the reviews file

  $ cd client
  $ echo "dummy" > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .

  $ echo "foo" >> foo
  $ hg commit -m 'Bug 1 - second commit'
  $ hg push ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:be8ff4f28043
  summary:    Bug 1 - second commit
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ cat .hg/reviews
  u http://localhost:$HGPORT1
  r ssh://user@dummy/$TESTTMP/server
  p bz://1/mynick 1
  c be8ff4f2804309fdbe6048ff76559f8e391ce765 2
  pc be8ff4f2804309fdbe6048ff76559f8e391ce765 1

  $ ls .hg/reviewboard/review
  1.state
  2.state

  $ cat .hg/reviewboard/review/1.state
  status pending
  $ cat .hg/reviewboard/review/2.state
  status pending

  $ cd ..
  $ rbmanage stop rbserver
  $ dockercontrol stop-bmo rb-test-store
  stopped 2 containers
