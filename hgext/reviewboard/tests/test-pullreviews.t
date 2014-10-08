#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-pullreviews
  $ cd client

Pulling with no reviews should result in error

  $ hg pullreviews
  abort: We don't know of any review servers. Try creating a review first.
  [255]

Seed the repo

  $ echo 'foo0' > foo0
  $ hg commit -A -m 'foo0'
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
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 123 - Foo 2'
  adding foo2
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 2 files
  submitting 2 changesets for review
  
  changeset:  1:775aa9c61e2b
  summary:    Bug 123 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:c90aa97490e2
  summary:    Bug 123 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

Pulling reviews with no changes

  $ hg pullreviews
  updated 3 reviews

  $ cd ..
  $ rbmanage rbserver stop

  $ dockercontrol stop-bmo rb-test-pullreviews > /dev/null
