#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug-range TestProduct TestComponent 2
  created bugs 1 to 2

Set up repo

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ echo foo2 > foo
  $ hg commit -m 'second commit'

  $ hg phase --public -r 0

Do the initial review

  $ hg push -r 1 --reviewid 1
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  
  changeset:  1:cd3395bd3f8a
  summary:    second commit
  review:     http://*:$HGPORT1/r/2 (pending) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (pending) (glob)
  (visit review url to publish this review request so others can see it)

Pushing with a different review ID will create a "duplicate" review

  $ hg push -r 1 --reviewid 2
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:cd3395bd3f8a
  summary:    second commit
  review:     http://*:$HGPORT1/r/4 (pending) (glob)
  
  review id:  bz://2/mynick
  review url: http://*:$HGPORT1/r/3 (pending) (glob)
  (visit review url to publish this review request so others can see it)
  [1]

  $ cat .hg/reviews
  u http://*:$HGPORT1 (glob)
  r ssh://*:$HGPORT6/test-repo (glob)
  p bz://1/mynick 1
  p bz://2/mynick 3
  c cd3395bd3f8a2108fb3178d6b1ec6077ca2bdbee 2
  c cd3395bd3f8a2108fb3178d6b1ec6077ca2bdbee 4
  pc cd3395bd3f8a2108fb3178d6b1ec6077ca2bdbee 1
  pc cd3395bd3f8a2108fb3178d6b1ec6077ca2bdbee 3

  $ hg log --template "{reviews % '{get(review, \"url\")}\n'}"
  http://*:$HGPORT1/r/2 (glob)
  http://*:$HGPORT1/r/4 (glob)

Cleanup

  $ mozreview stop
  stopped 8 containers
