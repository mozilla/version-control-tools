  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server
  $ serverconfig server/.hg/hgrc
  $ clientconfig client/.hg/hgrc

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ echo "rebase=" >> client/.hg/hgrc
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc
  $ echo "server_monkeypatch = ${TESTDIR}/hgext/reviewboard/tests/dummy_rbpost.py" >> server/.hg/hgrc

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ echo 'foo2' > foo
  $ hg commit -m 'foo2'
  $ hg push --reviewid 123 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  identified 1 changesets for review
  review identifier: bz://123
  review url: http://dummy/r/1
  
  changeset:  1:c3480b3f6944
  summary:    foo2
  review:     http://dummy/r/2

Now create a new head and push a rebase

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'bar' > bar
  $ hg commit -A -m 'bar'
  adding bar
  created new head
  $ hg rebase -s 1 -d .
  $ hg up tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg push --reviewid 123 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to 1 files (+1 heads)
  identified 2 changesets for review
  review identifier: bz://123
  review url: http://dummy/r/1
  
  changeset:  3:5003cd557db3
  summary:    foo2
  review:     http://dummy/r/2
  
  changeset:  2:e7315a409763
  summary:    bar
  review:     http://dummy/r/3
