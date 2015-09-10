#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

  $ python -m vcsreplicator.consumer $TESTTMP/vcsreplicator.ini --dump
  - name: heartbeat-1
  - name: hg-repo-init-1
    path: '{moz}/mozilla-central'

  $ python -m vcsreplicator.consumer $TESTTMP/vcsreplicator.ini --onetime
  $ python -m vcsreplicator.consumer $TESTTMP/vcsreplicator.ini --onetime
  TODO got a hg init message for $TESTTMP/repos/mozilla-central

Cleanup

  $ hgmo stop
