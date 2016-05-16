  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Cloning to an existing directory that isn't a hg checkout will abort

  $ mkdir dest
  $ touch dest/file0

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision tip
  ensuring http://localhost:$HGPORT/repo0@tip is available at dest
  abort: destination exists but no .hg directory
  [255]

file0 should still be present

  $ ls dest
  file0
