#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent summary

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF
  $ echo "obs=$TESTTMP/obs.py" >> client/.hg/hgrc
  $ echo "histedit=" >> client/.hg/hgrc

  $ cd client
  $ echo 'foo' > foo0
  $ hg commit -A -m 'root commit'
  adding foo0
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 1 - Foo 1'
  adding foo1
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 1 - Foo 2'
  adding foo2

  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  submitting 2 changesets for review
  
  changeset:  1:a252038ad074
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:c3d0947fefb7
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 1 - Foo 3'
  adding foo3
  $ echo 'foo4' > foo4
  $ hg commit -A -m 'Bug 1 - Foo 4'
  adding foo4
  $ echo 'foo5' > foo5
  $ hg commit -A -m 'Bug 1 - Foo 5'
  adding foo5

  $ hg histedit a252038ad074 --commands - 2>&1 <<EOF
  > pick a252038ad074 Foo 1
  > fold de473ef3c9d2 Foo 3
  > pick c3d0947fefb7 Foo 2
  > fold f5691a90b4d0 Foo 4
  > pick d86c61a23fc8 Foo 5
  > EOF
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  saved backup bundle to * (glob)
  saved backup bundle to * (glob)

  $ rbmanage publish $HGPORT1 1
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to ? files (+1 heads) (glob)
  submitting 3 changesets for review
  
  changeset:  6:4726ad3f958d
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  7:a17cc6746ab4
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  8:35fb57be1151
  summary:    Bug 1 - Foo 5
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

Cleanup

  $ mozreview stop
  stopped 5 containers
