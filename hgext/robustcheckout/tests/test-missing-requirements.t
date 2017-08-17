  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at local
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Blow out content of .hg directory to simulate a rolled back repo or something

  $ rm -rf local share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/*

  $ hg robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at local
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Shared store should be a modern repo
TODO this is buggy

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  cat: share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires: No such file or directory
  [1]

Test a variation where the local repo still exists

  $ rm -rf share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/*

  $ hg robustcheckout http://localhost:$HGPORT/repo0 local --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at local
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  warning: ignoring unknown working parent 5d6cdc75a09b!
  (pulling to obtain 5d6cdc75a09b)
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  cat: share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires: No such file or directory
  [1]

  $ rm -rf share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3

Test behavior when fncache is missing

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-existing --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at requires-existing
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  dotencode
  fncache
  generaldelta
  revlogv1
  store

  $ cat > share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires << EOF
  > generaldelta
  > revlogv1
  > store
  > EOF

TODO this should blow away legacy store

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-existing --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at requires-existing
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  generaldelta
  revlogv1
  store

  $ cat > share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires << EOF
  > generaldelta
  > revlogv1
  > store
  > EOF

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 requires-missing --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at requires-missing
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/requires
  generaldelta
  revlogv1
  store
