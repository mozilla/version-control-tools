  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Specifying an upstream repo will clone from it and pull from normal repo

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --upstream http://localhost:$HGPORT/repo0-upstream --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (cloning from upstream repo http://$LOCALHOST:$HGPORT/repo0-upstream)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  6 files to transfer, 411 bytes of data
  transferred 411 bytes in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  no changes found
  new changesets b8b78f0253d8 (?)
  (pulling to obtain 5d6cdc75a09b)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 5d6cdc75a09b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  new changesets 5d6cdc75a09b (?)
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Confirm no errors in log

  $ cat ./server/error.log
