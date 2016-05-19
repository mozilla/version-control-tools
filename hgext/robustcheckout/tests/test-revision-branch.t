  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Must specify revision or branch argument

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest
  abort: must specify one of --revision or --branch
  [255]

Only 1 of revision and branch can be specified

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --branch default --revision 5d6cdc75a09b
  abort: cannot specify both --revision and --branch
  [255]

A SHA-1 fragment is required in --revision argument

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision default
  abort: --revision must be a SHA-1 fragment 12-40 characters long
  [255]

It must be 12+ characters long

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 0123456789a
  abort: --revision must be a SHA-1 fragment 12-40 characters long
  [255]

It can't be more than 40 characters

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 01234567890123456789012345678901234567890
  abort: --revision must be a SHA-1 fragment 12-40 characters long
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

Create a branch that looks like a SHA-1 but isn't and verify we refuse to accept
updating to it

  $ cd dest
  $ hg branch abcdef0123456
  marked working directory as branch abcdef0123456
  $ echo nosha1 > foo
  $ hg commit -m 'ambiguous branch'
  $ cd ..

  $ hg robustcheckout http://localhost:$HGPORT/repo0 ambiguous --revision abcdef0123456
  ensuring http://localhost:$HGPORT/repo0@abcdef0123456 is available at ambiguous
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  abort: --revision argument is ambiguous
  (must be the first 12+ characters of a SHA-1 fragment)
  [255]
