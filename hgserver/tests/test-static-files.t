#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

/static/ serves hgtemplates static files

  $ http ${HGWEB_0_URL}static/style.css --body-file body
  200
  accept-ranges: bytes
  connection: close
  content-length: * (glob)
  content-type: text/css
  date: * (glob)
  etag: * (glob)
  last-modified: * (glob)
  server: Apache
  strict-transport-security: max-age=31536000
  vary: Accept-Encoding
  x-content-type-options: nosniff

  $ head -n 1 body
  a { text-decoration:none; }

  $ hgmo clean
