#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-print-offsets /etc/mercurial/vcsreplicator.ini
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

  $ hgmo clean
