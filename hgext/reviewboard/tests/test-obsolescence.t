#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ echo "rebase=" >> client/.hg/hgrc
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

  $ bugzilla create-bug TestProduct TestComponent 1

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ echo 'foo2' > foo
  $ hg commit -m 'foo2'
  $ hg push --reviewid 1
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  
  changeset:  1:c3480b3f6944
  summary:    foo2
  review:     http://*:$HGPORT1/r/2 (pending) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (pending) (glob)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish 1

Now create a new head and push a rebase

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'bar' > bar
  $ hg commit -A -m 'bar'
  adding bar
  created new head
  $ hg -q rebase -s 1 -d .
  $ hg up tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg push --reviewid 1
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to ? files (+1 heads) (glob)
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  2:e7315a409763
  summary:    bar
  review:     http://*:$HGPORT1/r/3 (pending) (glob)
  
  changeset:  3:5003cd557db3
  summary:    foo2
  review:     http://*:$HGPORT1/r/2 (pending) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (pending) (glob)
  (visit review url to publish this review request so others can see it)

Cleanup

  $ mozreview stop
  stopped 8 containers
