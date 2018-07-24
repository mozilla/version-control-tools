  $ . $TESTDIR/hgext/serverlog/tests/helpers.sh
  $ localext

  $ hg init server
  $ hg clone ssh://user@dummy/$TESTTMP/server repo0
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd repo0
  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

  $ cd ..

  $ cat server/.hg/blackbox.log
  *> *: BEGIN_SSH_SESSION $TESTTMP/server * (glob)
  *> *:* BEGIN_SSH_COMMAND hello (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND between (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND protocaps (glob) (hg46 !)
  *> *:* END_SSH_COMMAND * * (glob) (hg46 !)
  *> *:* BEGIN_SSH_COMMAND batch (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* BEGIN_SSH_COMMAND getbundle (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *:* END_SSH_COMMAND * * (glob) (no-hg46 !)
  *> *: END_SSH_SESSION * * (glob)
  *> *: BEGIN_SSH_SESSION $TESTTMP/server * (glob)
  *> *: BEGIN_SSH_COMMAND hello (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND between (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND protocaps (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND batch (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND listkeys (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND listkeys (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND unbundle (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: BEGIN_SSH_COMMAND listkeys (glob)
  *> *:* END_SSH_COMMAND * * (glob)
  *> *: END_SSH_SESSION * * (glob)
