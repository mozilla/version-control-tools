  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Must specify revision or branch argument

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest
  abort: must specify one of --revision or --branch
  [255]

Only 1 of revision and branch can be specified

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --branch default --revision 5d6cdc75a09b
  abort: cannot specify both --revision and --branch
  [255]

Specifying branch argument will checkout branch

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --branch default
  ensuring http://localhost:$HGPORT/repo0@default is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  searching for changes
  no changes found
  (pulling to obtain default)
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Specifying branch argument will always attempt to pull because branch revisions can change

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --branch default
  ensuring http://localhost:$HGPORT/repo0@default is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain default)
  no changes found
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Updating to another branch works

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --branch branch1
  ensuring http://localhost:$HGPORT/repo0@branch1 is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain branch1)
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Specifying revision will switch away from branch

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
