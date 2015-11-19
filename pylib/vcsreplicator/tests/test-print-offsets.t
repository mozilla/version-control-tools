#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /repo/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
  topic     group           partition    offset    available    lag (s)
  --------  ------------  -----------  --------  -----------  ---------
  pushdata  *           0         1            1          0 (glob)
  pushdata  *           1         0            0          0 (glob)
  pushdata  *           2         1            1          0 (glob)
  pushdata  *           3         0            0          0 (glob)
  pushdata  *           4         0            0          0 (glob)
  pushdata  *           5         0            0          0 (glob)
  pushdata  *           6         0            0          0 (glob)
  pushdata  *           7         0            0          0 (glob)

Cleanup

  $ hgmo stop
