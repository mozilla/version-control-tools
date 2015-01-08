#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-multiple-precursors

  $ bugzilla create-bug-range TestProduct TestComponent 123
  created bugs 1 to 123

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

  $ cd client
  $ echo 'foo' > foo0
  $ hg commit -A -m 'root commit'
  adding foo0
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 123 - Foo 1'
  adding foo1
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:c5b850e24951
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

Splitting the changeset results in multiple reviews

  $ hg up -r 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 123 - Foo 2'
  adding foo2
  created new head
  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 123 - Foo 3'
  adding foo3
  $ hg debugobsolete -d '0 0' c5b850e249510046906bcb24f774635c4521a4a9 05451502b94b2b05f1dd640074d4c0aa7985f52f 9d5db6367f324fad46508f44086ddbc7c79eda0e

  $ rbmanage publish $HGPORT1 1
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files (+1 heads)
  submitting 2 changesets for review
  
  changeset:  2:05451502b94b
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  3:9d5db6367f32
  summary:    Bug 123 - Foo 3
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ cd ..
  $ rbmanage stop rbserver

  $ dockercontrol stop-bmo rb-test-multiple-precursors
  stopped 2 containers
