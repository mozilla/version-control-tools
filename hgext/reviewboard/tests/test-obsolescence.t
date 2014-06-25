  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server
  $ rbmanage rbserver create
  $ rbmanage rbserver repo test-repo http://localhost:$HGPORT2/
  $ rbmanage rbserver start $HGPORT
  $ serverconfig server/.hg/hgrc $HGPORT
  $ clientconfig client/.hg/hgrc
  $ hg serve -R server -d -p $HGPORT2 --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ echo "rebase=" >> client/.hg/hgrc
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

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
  submitting 1 changesets for review
  
  changeset:  1:c3480b3f6944
  summary:    foo2
  review:     http://localhost:$HGPORT/r/2
  
  review id:  bz://123
  review url: http://localhost:$HGPORT/r/1

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
  submitting 2 changesets for review
  
  changeset:  2:e7315a409763
  summary:    bar
  review:     http://localhost:$HGPORT/r/3
  
  changeset:  3:5003cd557db3
  summary:    foo2
  review:     http://localhost:$HGPORT/r/2
  
  review id:  bz://123
  review url: http://localhost:$HGPORT/r/1
