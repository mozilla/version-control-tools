#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

HSTS header should be present on normal HTTP requests

  $ http ${HGWEB_0_URL}mozilla-central --no-body --header strict-transport-security
  200
  strict-transport-security: max-age=31536000

HSTS header absent on protocol requests

  $ http ${HGWEB_0_URL}mozilla-central?cmd=capabilities --no-body --header strict-transport-security
  200

HSTS header absent from Mercurial user agents

  $ http ${HGWEB_0_URL}mozilla-central --agent 'mercurial/proto-1.0' --no-body --header strict-transport-security
  200

  $ http ${HGWEB_0_URL}mozilla-central --agent 'mercurial/proto-1.0 (Mercurial 3.9)' --no-body --header strict-transport-security
  200

HSTS header absent if both conditions are true

  $ http ${HGWEB_0_URL}mozilla-central?cmd=capabilities --agent 'mercurial/proto-1.0' --no-body --header strict-transport-security
  200
