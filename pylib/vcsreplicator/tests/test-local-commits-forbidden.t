#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create the repository

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

Adding a commit locally is not allowed

  $ hgmo exec hgssh touch /repo/hg/mozilla/mozilla-central/foo
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central add
  adding ../repo/hg/mozilla/mozilla-central/foo
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central commit -m initial
  cannot commit to replicating repositories; push instead
  abort: precommit.vcsreplicator hook failed
  [255]

Cleanup

  $ hgmo clean
