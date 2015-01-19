#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-obsolescence

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ echo "rebase=" >> client/.hg/hgrc
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

  $ bugzilla create-bug-range TestProduct TestComponent 123
  created bugs 1 to 123

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
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish $HGPORT1 1

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
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  3:5003cd557db3
  summary:    foo2
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ cd ..
  $ rbmanage stop rbserver

  $ dockercontrol stop-bmo rb-test-obsolescence
  stopped 3 containers
