#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Creating a repo outside of the managed path should raise an error

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg init /tmp/repo0
  abort: repository path not configured for replication
  (add entry to [replicationpathrewrites])
  [255]

Trying to replicate a repo outside of a managed path should raise an error
(this assumes `hg init` doesn't delete the repo when replication fails, which is
a poor assertion)

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /tmp/repo0 replicatesync
  abort: repository path not configured for replication
  (add entry to [replicationpathrewrites])
  [255]

Cleanup

  $ hgmo clean
