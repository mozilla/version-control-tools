  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  7 files to transfer, 1.08 KB of data (hg67 !)
  6 files to transfer, 1.08 KB of data (no-hg67 !)
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  new changesets b8b78f0253d8:aada1b3e573f (?)
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Modifications to a tracked file should get lost during update

  $ cat dest/foo
  1

  $ cat > dest/foo << EOF
  > modified
  > EOF

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cat dest/foo
  1

Modifications should also get lost when updating to new revision

  $ cat > dest/foo << EOF
  > modified
  > EOF

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision b8b78f0253d8
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@b8b78f0253d8 is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to b8b78f0253d822e33ba652fd3d80a5c0837cfdf3

  $ cat dest/foo

Added and copied files will be lost during update

  $ cd dest
  $ touch bar
  $ hg add bar
  $ hg mv foo baz
  $ cd ..

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ hg -R dest status
  ? bar
  ? baz

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b --purge
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ hg -R dest status

Confirm no errors in log

  $ cat ./server/error.log
