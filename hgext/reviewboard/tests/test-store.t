  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server

  $ serverconfig server/.hg/hgrc
  $ cat >> server/.hg/hgrc << EOF
  > server_monkeypatch = $TESTDIR/hgext/reviewboard/tests/dummy_rbpost.py
  > EOF

  $ clientconfig client/.hg/hgrc

  $ cat >> client/.hg/hgrc << EOF
  > [paths]
  > default-push = ssh://user@dummy/$TESTTMP/server
  > EOF

Pushing a review will create the reviews file

  $ cd client
  $ echo "dummy" > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .
  $ hg bookmark test-bookmark

  $ echo "foo" >> foo
  $ hg commit -m 'second commit'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: test-bookmark
  This will get printed on the client

  $ cat .hg/reviews
  n a287f990367776cdfa5c7351f71304450e4822b4 2
