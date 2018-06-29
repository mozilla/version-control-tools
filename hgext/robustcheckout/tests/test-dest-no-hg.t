  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Cloning to an existing directory that isn't a hg checkout will abort

  $ mkdir dest
  $ touch dest/file0

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest
  abort: destination exists but no .hg directory
  [255]

file0 should still be present

  $ ls dest
  file0

Confirm no errors in log

  $ cat ./server/error.log
