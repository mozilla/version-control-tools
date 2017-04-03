#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create a dummy repo

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

HTTP POST should be used for some HTTP requests

  $ hg -q clone ${HGWEB_0_URL}mozilla-central clone
  $ hgmo exec hgweb0 cat /var/log/httpd/hg.mozilla.org/access_log
  $DOCKER_HOSTNAME - - [*] "GET /mozilla-central?cmd=capabilities HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  $DOCKER_HOSTNAME - - [*] "POST /mozilla-central?cmd=batch HTTP/1.1" 200 42 "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  $DOCKER_HOSTNAME - - [*] "POST /mozilla-central?cmd=getbundle HTTP/1.1" 200 102 "-" "mercurial/proto-1.0 (Mercurial *)" (glob)

Cleanup

  $ hgmo clean
