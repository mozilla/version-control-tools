#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo try scm_level_1
  (recorded repository creation in replication log)

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/try
  $ cd try
  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ cd ..

  $ scm3user

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/mozilla-central
  $ cd mozilla-central
  $ echo 1 > foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ cd ..

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/moz-owner
  scm_level_3

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/try/.hg/moz-owner
  scm_level_1

  $ hgmo clean
