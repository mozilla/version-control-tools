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

  $ echo "foo" >> foo
  $ hg commit -m 'Bug 456 - second commit'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  identified 1 changesets for review
  review identifier: bz://456
  created review request: 1
  
  changeset:  1:7f387c765e68
  summary:    Bug 456 - second commit
  review:     http://dummy/r/2

  $ cat .hg/reviews
  u http://dummy
  p bz://456 1
  c 7f387c765e685da95d7a4ffab2ccf06548c06fcf 2
