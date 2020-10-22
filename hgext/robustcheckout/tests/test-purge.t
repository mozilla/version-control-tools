  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Not specifying --purge won't purge checkout

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  6 files to transfer, 1.08 KB of data
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  no changes found
  new changesets b8b78f0253d8:aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ touch dest/file0
  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ ls dest
  file0
  foo

Specifying purge will delete files

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b --purge
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ ls dest
  foo

Ignored files are also purged when requested

  $ cd dest
  $ cat > .hgignore << EOF
  > .pyc$
  > EOF
  $ hg -q commit -A -m hgignore

  $ touch foo.pyc
  $ cd ..

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ ls dest
  foo
  foo.pyc

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b --purge
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce
  $ ls dest
  foo

Try running `hg purge` outside of robustcheckout

  $ hg -R dest/ purge

Confirm no errors in log

  $ cat ./server/error.log
