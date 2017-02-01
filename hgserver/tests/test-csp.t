#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

CSP header should be present on normal HTTP requests

  $ http ${HGWEB_0_URL}mozilla-central/shortlog --header content-security-policy | grep script
  content-security-policy: default-src 'none'; connect-src 'self' https://bugzilla.mozilla.org/; img-src 'self'; script-src 'self' 'nonce-*'; style-src 'self' 'unsafe-inline'; upgrade-insecure-requests (glob)
  <script type="text/javascript" src="/mozilla-central/static/mercurial.js"></script>
  <script type="text/javascript" nonce="*"> (glob)
  </script>

CSP header absent on protocol requests

  $ http ${HGWEB_0_URL}mozilla-central?cmd=capabilities --no-body --header content-security-policy
  200

CSP header absent from Mercurial user agents

  $ http ${HGWEB_0_URL}mozilla-central --agent 'mercurial/proto-1.0' --no-body --header content-security-policy
  200

  $ http ${HGWEB_0_URL}mozilla-central --agent 'mercurial/proto-1.0 (Mercurial 3.9)' --no-body --header content-security-policy
  200

CSP header absent if both conditions are true

  $ http ${HGWEB_0_URL}mozilla-central?cmd=capabilities --agent 'mercurial/proto-1.0' --no-body --header content-security-policy
  200

reftest analyzer is a special snowflake

  $ http ${HGWEB_0_URL}mozilla-central/raw-file/tip/layout/tools/reftest/reftest-analyzer.xhtml --no-body --header content-security-policy
  200
  content-security-policy: default-src 'none'; connect-src 'self' https://archive.mozilla.org/ https://public-artifacts.taskcluster.net/ https://queue.taskcluster.net/; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; upgrade-insecure-requests

  $ http "${HGWEB_0_URL}mozilla-central/raw-file/tip/layout/tools/reftest/reftest-analyzer.xhtml#logurl=https://queue.taskcluster.net/v1/task/KQYN-Sa9TBmXR3m8GaXXwg/runs/0/artifacts/public/logs/live_backing.log&only_show_unexpected=1" --no-body --header content-security-policy
  200
  content-security-policy: default-src 'none'; connect-src 'self' https://archive.mozilla.org/ https://public-artifacts.taskcluster.net/ https://queue.taskcluster.net/; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; upgrade-insecure-requests

No CSP if HG user-agent

  $ http ${HGWEB_0_URL}mozilla-central/raw-file/tip/layout/tools/reftest/reftest-analyzer.xhtml --agent 'mercurial/proto-1.0' --no-body --header content-security-policy
  200
