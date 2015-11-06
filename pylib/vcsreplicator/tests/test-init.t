#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repository should record an event saying so

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

Cleanup

  $ hgmo stop
