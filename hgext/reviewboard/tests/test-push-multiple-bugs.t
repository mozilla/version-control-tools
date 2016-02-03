#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-push-multiple-bugs

  $ cd client

  $ echo foo > foo
  $ hg commit -A -m 'Bug 1 - Great bug'
  adding foo
  $ echo foo2 > foo
  $ hg commit -A -m 'Bug 2 - Also an outstanding bug'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/809a72bb9607-4f7b536f-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  abort: cannot submit reviews referencing multiple bugs
  (limit reviewed changesets with "-c" or "-r" arguments)
  [255]

Cleanup

  $ mozreview stop
  stopped 9 containers
