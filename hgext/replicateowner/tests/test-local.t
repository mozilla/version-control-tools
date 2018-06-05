  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > [extensions]
  > replicateowner = $TESTDIR/hgext/replicateowner
  > EOF

  $ hg init server

#if hg46

Wire protocol command works

  $ hg -R server debugwireproto --localssh << EOF
  > command mozowner
  > EOF
  creating ssh peer from handshake results
  sending mozowner command
  response: b'*' (glob)

#endif

`hg pull` calls the mozowner command

  $ hg init client

  $ hg -R client pull ssh://user@dummy/$TESTTMP/server
  pulling from ssh://user@dummy/$TESTTMP/server
  no changes found
  updating moz-owner file

  $ cat client/.hg/moz-owner
  * (glob)

Subsequent pull should no-op

  $ hg -R client pull ssh://user@dummy/$TESTTMP/server
  pulling from ssh://user@dummy/$TESTTMP/server
  no changes found

Modifying the file should update file

  $ echo dummy > client/.hg/moz-owner
  $ hg -R client pull ssh://user@dummy/$TESTTMP/server
  pulling from ssh://user@dummy/$TESTTMP/server
  no changes found
  updating moz-owner file
