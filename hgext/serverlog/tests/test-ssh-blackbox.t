  $ . $TESTDIR/hgext/serverlog/tests/helpers.sh
  $ localext

  $ hg init server
  $ hg clone ssh://user@dummy/$TESTTMP/server repo0
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cat server/.hg/blackbox.log
  *> *: BEGIN_SSH_SESSION $TESTTMP/server * (glob)
  *> *:* BEGIN_SSH_COMMAND hello (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND between (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND batch (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND getbundle (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: END_SSH_SESSION * * (glob)
