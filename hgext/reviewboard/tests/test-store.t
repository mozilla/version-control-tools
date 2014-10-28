#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-store

Pushing a review will create the reviews file

  $ cd client
  $ echo "dummy" > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .

  $ echo "foo" >> foo
  $ hg commit -m 'Bug 456 - second commit'
  $ hg push ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:7f387c765e68
  summary:    Bug 456 - second commit
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://456/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ cat .hg/reviews
  u http://localhost:$HGPORT1
  r ssh://user@dummy/$TESTTMP/server
  p bz://456/mynick 1
  c 7f387c765e685da95d7a4ffab2ccf06548c06fcf 2
  pc 7f387c765e685da95d7a4ffab2ccf06548c06fcf 1

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
