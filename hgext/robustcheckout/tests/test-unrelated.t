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
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Attempting to pull/checkout an unrelated repo will blow away the destination

  $ touch dest/file0
  $ hg robustcheckout http://localhost:$HGPORT/repo1 dest --revision 7d5b54cb09e1
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain 7d5b54cb09e1)
  searching for changes
  (repository is unrelated; deleting)
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at dest
  (sharing from new pooled repository 65cd4e3b46a3f22a08ec4162871e67f57c322f6a)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70

  $ ls dest
  foo

And again for safe measure

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg)
  (pulling to obtain 5d6cdc75a09b)
  searching for changes
  (repository is unrelated; deleting)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
