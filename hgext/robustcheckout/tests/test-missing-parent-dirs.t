  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Missing parent of destination directory will be created automatically

  $ hg robustcheckout http://localhost:$HGPORT/repo0 parent0/parent1/dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at parent0/parent1/dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  7 files to transfer, 1.08 KB of data (hg67 !)
  6 files to transfer, 1.08 KB of data (no-hg67 !)
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  new changesets b8b78f0253d8:aada1b3e573f (?)
  no changes found
  new changesets b8b78f0253d8:aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Missing parent of share pool directory will be created automatically

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b --sharebase shareparent/sharebase
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  7 files to transfer, 1.08 KB of data (hg67 !)
  6 files to transfer, 1.08 KB of data (no-hg67 !)
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  no changes found
  new changesets b8b78f0253d8:aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Confirm no errors in log

  $ cat ./server/error.log
