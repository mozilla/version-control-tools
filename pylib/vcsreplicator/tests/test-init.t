#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo exec hgweb0 ls /repo/hg/mozilla

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

  $ consumer --dump
  - name: heartbeat-1
  - name: hg-repo-init-1
    path: '{moz}/mozilla-central'

  $ consumer --onetime
  $ consumer --onetime
  WARNING:vcsreplicator.consumer:created Mercurial repository: $TESTTMP/repos/mozilla-central

  $ hgmo exec hgweb0 cat /var/log/supervisor/vcsreplicator.log
  No handlers could be found for logger "kafka.conn"
  WARNING:vcsreplicator.consumer:created Mercurial repository: /repo/hg/mozilla/mozilla-central

  $ hgmo exec hgweb0 ls /repo/hg/mozilla
  mozilla-central

Cleanup

  $ hgmo stop
