#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-push-invalid-bug

  $ cd client

  $ echo foo > foo
  $ hg commit -A -m 'Bug 100 - Not an existing bug'
  adding foo
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  abort: bug 100 does not exist; please change the review id (bz://100/mynick)
  [255]

TODO Test for confidential bugs when Bugzilla's API enables it

Cleanup

  $ mozreview stop
  stopped 8 containers
