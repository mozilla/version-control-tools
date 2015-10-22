#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent 1

Pushing a review will create the reviews file

  $ cd client
  $ echo "dummy" > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .

  $ echo "foo" >> foo
  $ hg commit -m 'Bug 1 - second commit'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/be8ff4f28043*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:00a4f82beb7c
  summary:    Bug 1 - second commit
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ cat .hg/reviews
  u http://*:$HGPORT1 (glob)
  r ssh://*:$HGPORT6/test-repo (glob)
  p bz://1/mynick 1
  c 00a4f82beb7c11fa00dafd1d2e613d979171154f 2
  pc 00a4f82beb7c11fa00dafd1d2e613d979171154f 1

  $ ls .hg/reviewboard/review
  1.state
  2.state

  $ cat .hg/reviewboard/review/1.state
  public False
  status pending
  $ cat .hg/reviewboard/review/2.state
  public False
  status pending

Cleanup

  $ mozreview stop
  stopped 10 containers
