#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

HSTS header should be present on normal HTTP requests

  $ http ${MERCURIAL_URL}/test-repo --no-body --header strict-transport-security
  200
  strict-transport-security: max-age=300

HSTS header absent on protocol requests

  $ http ${MERCURIAL_URL}/test-repo?cmd=capabilities --no-body --header strict-transport-security
  200
  strict-transport-security: max-age=300

HSTS header absent from Mercurial user agents

  $ http ${MERCURIAL_URL}/test-repo --agent 'mercurial/proto-1.0' --no-body --header strict-transport-security
  200

  $ http ${MERCURIAL_URL}/test-repo --agent 'mercurial/proto-1.0 (Mercurial 3.9)' --no-body --header strict-transport-security
  200

HSTS header absent if both conditions are true

  $ http ${MERCURIAL_URL}/test-repo?cmd=capabilities --agent 'mercurial/proto-1.0' --no-body --header strict-transport-security
  200

  $ mozreview stop
  stopped 7 containers
