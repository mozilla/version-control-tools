#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser
  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

Mercurial SSH session is logged in syslog

  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  destination directory: mozilla-central
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hgmo exec hgssh grep hgweb /var/log/hg.log
  * hgweb: *: BEGIN_SSH_SESSION mozilla-central user@example.com (glob)
  * hgweb: *:* BEGIN_SSH_COMMAND hello (glob)
  * hgweb: *:* END_SSH_COMMAND * * (glob)
  * hgweb: *:* BEGIN_SSH_COMMAND between (glob)
  * hgweb: *:* END_SSH_COMMAND * * (glob)
  * hgweb: *:* BEGIN_SSH_COMMAND batch (glob)
  * hgweb: *:* END_SSH_COMMAND * * (glob)
  * hgweb: *:* BEGIN_SSH_COMMAND getbundle (glob)
  * hgweb: *:* END_SSH_COMMAND * * (glob)
  * hgweb: *:* END_SSH_COMMAND * * (glob)
  * hgweb: *: END_SSH_SESSION * * (glob)

  $ hgmo clean
