#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

  $ cd client

Pulling with no reviews should result in error

  $ hg fetchreviews
  abort: We don't know of any review servers. Try creating a review first.
  [255]

Seed the repo

  $ echo 'foo0' > foo0
  $ hg commit -A -m 'foo0'
  adding foo0
  $ hg push --noreview
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 1 - Foo 1'
  adding foo1
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 1 - Foo 2'
  adding foo2
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  1:2b77e5337389
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:19006c154c5f
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish 1

Pulling reviews with no changes

  $ hg fetchreviews
  updated 3 reviews

Cleanup

  $ mozreview stop
  stopped 8 containers
