  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets b8b78f0253d8:aada1b3e573f (?)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
  $ hg -R dest --config extensions.strip= strip -r aada1b3e573f --no-backup

Corrupt the manifest

  $ cat >> $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/store/00manifest.i << EOF
  > baddata
  > EOF

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain aada1b3e573f)
  searching for changes
  adding changesets
  adding manifests
  transaction abort!
  rollback completed
  (repo corruption: index 00manifest.i is corrupted; deleting shared store)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (shared store does not exist; deleting destination)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets b8b78f0253d8:aada1b3e573f (?)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Now check corruption is handled during clone

  $ hg -R dest --config extensions.strip= strip -r aada1b3e573f --no-backup
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cat >> $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/store/00manifest.i << EOF
  > baddata
  > EOF
  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest1 --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest1
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  adding changesets
  adding manifests
  transaction abort!
  rollback completed
  (repo corruption: index 00manifest.i is corrupted; deleting shared store)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest1
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (shared store does not exist; deleting destination)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets b8b78f0253d8:aada1b3e573f (?)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Confirm no errors in log

  $ cat ./server/error.log
