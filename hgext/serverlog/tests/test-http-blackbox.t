  $ . $TESTDIR/hgext/serverlog/tests/helpers.sh
  $ localext

  $ hg init server
  $ hg -R server serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid > $DAEMON_PIDS
  $ hg clone http://localhost:$HGPORT repo
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cat server/.hg/blackbox.log
  *> * BEGIN_REQUEST $TESTTMP/server $LOCALIP /?cmd=capabilities (glob)
  *> * BEGIN_PROTOCOL capabilities (glob)
  *> * END_REQUEST 0 * * (glob) (no-hg46 !)
  *> * END_REQUEST 458 * * (glob) (hg46 !)
  *> * BEGIN_REQUEST $TESTTMP/server $LOCALIP /?cmd=batch (glob)
  *> * BEGIN_PROTOCOL batch (glob)
  *> * END_REQUEST 0 * * (glob) (no-hg46 !)
  *> * END_REQUEST 42 * * (glob) (hg46 !)
  *> * BEGIN_REQUEST $TESTTMP/server $LOCALIP /?cmd=getbundle (glob)
  *> * BEGIN_PROTOCOL getbundle (glob)
  *> * END_REQUEST 82 * * (glob)
  $ cat error.log
