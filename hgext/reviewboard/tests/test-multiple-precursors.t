#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent summary

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
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  2:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)

Splitting the changeset results in multiple reviews

  $ hg up -r 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 1 - Foo 2'
  adding foo2
  created new head
  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 1 - Foo 3'
  adding foo3
  $ hg debugobsolete -d '0 0' c5b850e249510046906bcb24f774635c4521a4a9 05451502b94b2b05f1dd640074d4c0aa7985f52f 9d5db6367f324fad46508f44086ddbc7c79eda0e

  $ rbmanage publish 1
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:c5bd6809e957
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  4:f142ef54f825
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)

Cleanup

  $ mozreview stop
  stopped 10 containers
