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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 1 - Foo 1'
  adding foo1
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 1 - Foo 2'
  adding foo2

  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  4:dfe48634934b
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 1 - Foo 3'
  adding foo3
  $ echo 'foo4' > foo4
  $ hg commit -A -m 'Bug 1 - Foo 4'
  adding foo4
  $ echo 'foo5' > foo5
  $ hg commit -A -m 'Bug 1 - Foo 5'
  adding foo5

  $ hg histedit 6bd3fbee3dfa --commands - 2>&1 <<EOF
  > pick 6bd3fbee3dfa Foo 1
  > fold d751d4c04967 Foo 3
  > pick dfe48634934b Foo 2
  > fold 98dd6a7335db Foo 4
  > pick 76088734e3cb Foo 5
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

  $ rbmanage publish 1
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to ? files (+1 heads) (glob)
  remote: recorded push in pushlog
  submitting 3 changesets for review
  
  changeset:  8:dac4214a563a
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  9:5b936d238262
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  changeset:  10:ae82743c8863
  summary:    Bug 1 - Foo 5
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

Cleanup

  $ mozreview stop
  stopped 8 containers
