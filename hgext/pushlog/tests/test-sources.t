  $ . $TESTDIR/hghooks/tests/common.sh
  $ export USER=hguser
  $ hg init server
  $ configurepushlog server

  $ hg init client1
  $ hg clone server client2 > /dev/null
  $ configurepushlog client2

  $ cd client1
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server > /dev/null
  $ cd ..

Introducing changesets via pulling does not run the pushlog hook

  $ cd client2
  $ hg --verbose pull
  pulling from $TESTTMP/server
  requesting all changes
  1 changesets found
  uncompressed size of bundle content:
       182 (changelog)
       165 (manifests)
       115  foo
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  calling hook pretxnchangegroup.pushlog: hgext_pushlog.pretxnchangegrouphook
  (not updating pushlog since changesets come from pull)
  new changesets 96ee1d7354c4 (?)
  (run 'hg update' to get a working copy)

  $ dumppushlog client2
  pushlog database does not exist: $TESTTMP/client2/.hg/pushlog2.db
  [1]
