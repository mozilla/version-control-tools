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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/809a72bb9607-4f7b536f-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  It appears you are pushing commits for multiple bugs for review. Unfortunately, this is not currently supported (and bad things will happen.) You can use the -c option to specify an individual commit to be reviewed or use -r to restrict what is pushed.

Cleanup

  $ mozreview stop
  stopped 10 containers
