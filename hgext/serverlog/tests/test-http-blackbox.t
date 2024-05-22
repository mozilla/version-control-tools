  $ . $TESTDIR/hgext/serverlog/tests/helpers.sh
  $ localext
  $ cat >> $HGRCPATH << EOF
  > [serverlog]
  > syslog = false
  > hgweb = True
  > EOF

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
  *> * END_REQUEST * * * (glob)
  *> * BEGIN_REQUEST $TESTTMP/server $LOCALIP /?cmd=batch (glob)
  *> * BEGIN_PROTOCOL batch (glob)
  *> * END_REQUEST 42 * * (glob)
  *> * BEGIN_REQUEST $TESTTMP/server $LOCALIP /?cmd=getbundle (glob)
  *> * BEGIN_PROTOCOL getbundle (glob)
  *> * END_REQUEST 82 * * (glob)
  $ cat error.log
