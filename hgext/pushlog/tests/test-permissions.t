  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > 
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF

  $ export USER=hguser
  $ hg init server
  $ cd server
  $ hg serve -d -p $HGPORT --pid-file server.pid -E error.log -A access.log
  $ cat server.pid >> $DAEMON_PIDS
  $ cd ..

Error seen if permissions don't allow pushlog file creation

  $ chmod u-w server/.hg
  $ chmod g-w server/.hg

  $ hg clone ssh://user@dummy/$TESTTMP/server clone
  no changes found
  abort: remote error fetching pushlog: unable to open database file
  [255]
