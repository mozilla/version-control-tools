  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest0 --revision aada1b3e573f --noupdate
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo0@aada1b3e573f is available at dest0
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  streaming all changes
  6 files to transfer, 1.08 KB of data
  transferred 1.08 KB in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  no changes found
  (skipping update since `-U` was passed)

  $ ls -a dest0/
  .
  ..
  .hg
