  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at local
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Blow out content of .hg directory to simulate a rolled back repo or something

  $ rm -rf local share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/*

  $ hg robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at local
  (shared store missing requires file; this is a really odd failure; deleting store and destination)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  6 files to transfer, 1.08 KB of data
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  new changesets b8b78f0253d8:aada1b3e573f (?)
  no changes found
  new changesets b8b78f0253d8:aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Shared store should be a modern repo

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  sparserevlog (hg49 !)
  store

Test a variation where the local repo still exists

  $ rm -rf share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/*

  $ hg robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at local
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (shared store missing requires file; this is a really odd failure; deleting store and destination)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  6 files to transfer, 1.08 KB of data
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  no changes found
  new changesets b8b78f0253d8:aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  sparserevlog (hg49 !)
  store

  $ rm -rf share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3

Test behavior when fncache is missing

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-existing --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at requires-existing
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  sparserevlog (hg49 !)
  store

  $ cat > share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires << EOF
  > generaldelta
  > revlogv1
  > store
  > EOF

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-existing --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at requires-existing
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (shared store missing requirements: dotencode, fncache; deleting store and destination to ensure optimal behavior)
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  sparserevlog (hg49 !)
  store

  $ cat > share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires << EOF
  > generaldelta
  > revlogv1
  > store
  > EOF

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-missing --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at requires-missing
  (shared store missing requirements: dotencode, fncache; deleting store and destination to ensure optimal behavior)
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  sparserevlog (hg49 !)
  store

Confirm no errors in log

  $ cat ./server/error.log
