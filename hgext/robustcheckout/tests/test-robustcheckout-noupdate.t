  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest0 --revision aada1b3e573f --noupdate
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@aada1b3e573f is available at dest0
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets b8b78f0253d8:aada1b3e573f
  searching for changes
  no changes found
  (skipping update since `-U` was passed)

  $ ls -a dest0/
  .
  ..
  .hg
