#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

HSTS header should be present

  $ http ${HGWEB_0_URL}mozilla-central --no-body --header strict-transport-security
  200
  strict-transport-security: max-age=31536000

Cleanup

  $ hgmo clean
