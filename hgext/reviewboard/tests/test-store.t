  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server
  $ rbmanage rbserver create
  $ rbmanage rbserver repo test-repo http://localhost:$HGPORT1
  $ rbmanage rbserver start $HGPORT
  $ hg serve -R server -d -p $HGPORT1 --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ serverconfig server/.hg/hgrc $HGPORT
  $ clientconfig client/.hg/hgrc

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
  review:     http://localhost:$HGPORT/r/2
  
  review id:  bz://456
  review url: http://localhost:$HGPORT/r/1

  $ cat .hg/reviews
  u http://localhost:$HGPORT
  p bz://456 1
  c 7f387c765e685da95d7a4ffab2ccf06548c06fcf 2
  pc 7f387c765e685da95d7a4ffab2ccf06548c06fcf 1
