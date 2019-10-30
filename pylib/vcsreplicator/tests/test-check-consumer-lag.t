#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ alias check='hgmo exec hgweb0 /var/hg/venv_replication/bin/check_vcsreplicator_lag /etc/mercurial/vcsreplicator.ini'

Check should be OK by default

  $ check
  OK - 8/8 consumers completely in sync
  
  OK - partition 0 is completely in sync (0/0)
  OK - partition 1 is completely in sync (0/0)
  OK - partition 2 is completely in sync (0/0)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Stop the replication consumers to test failure scenarios

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop vcsreplicator:*
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)
  vcsreplicator:\d: stopped (re)

No issues reported when thresholds aren't met

  $ hgmo exec hgssh /create-repo repo0 scm_level_1
  (recorded repository creation in replication log)

  $ check
  OK - 2/8 consumers out of sync but within tolerances
  
  OK - partition 0 is 1 messages behind (0/1)
  OK - partition 0 is \d+\.\d+ seconds behind (re)
  OK - partition 1 is completely in sync (0/0)
  OK - partition 2 is 1 messages behind (0/1)
  OK - partition 2 is \d+\.\d+ seconds behind (re)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Warning reported when lag count hits threshold

  $ check --warning-lag-count 1
  WARNING - 2/8 partitions out of sync
  
  WARNING - partition 0 is 1 messages behind (0/1)
  OK - partition 0 is \d+\.\d+ seconds behind (re)
  OK - partition 1 is completely in sync (0/0)
  WARNING - partition 2 is 1 messages behind (0/1)
  OK - partition 2 is \d+\.\d+ seconds behind (re)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [1]

Critical reported when lag count hits threshold

  $ check --critical-lag-count 1
  CRITICAL - 2/8 partitions out of sync
  
  CRITICAL - partition 0 is 1 messages behind (0/1)
  OK - partition 0 is \d+\.\d+ seconds behind (re)
  OK - partition 1 is completely in sync (0/0)
  CRITICAL - partition 2 is 1 messages behind (0/1)
  OK - partition 2 is \d+\.\d+ seconds behind (re)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [2]

Warning reported when lag time hits threshold

  $ sleep 1

  $ check --warning-lag-time 0.9
  WARNING - 2/8 partitions out of sync
  
  OK - partition 0 is 1 messages behind (0/1)
  WARNING - partition 0 is \d+\.\d+ seconds behind (re)
  OK - partition 1 is completely in sync (0/0)
  OK - partition 2 is 1 messages behind (0/1)
  WARNING - partition 2 is \d+\.\d+ seconds behind (re)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [1]

Critical reported when lag time hits threshold

  $ check --critical-lag-time 0.9
  CRITICAL - 2/8 partitions out of sync
  
  OK - partition 0 is 1 messages behind (0/1)
  CRITICAL - partition 0 is \d+\.\d+ seconds behind (re)
  OK - partition 1 is completely in sync (0/0)
  OK - partition 2 is 1 messages behind (0/1)
  CRITICAL - partition 2 is \d+\.\d+ seconds behind (re)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [2]

Resuming consumers clears check

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start vcsreplicator:*
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)
  vcsreplicator:\d: started (re)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ check --warning-lag-count 0 --warning-lag-time 1.0
  OK - 8/8 consumers completely in sync
  
  OK - partition 0 is completely in sync (1/1)
  OK - partition 1 is completely in sync (0/0)
  OK - partition 2 is completely in sync (1/1)
  OK - partition 3 is completely in sync (0/0)
  OK - partition 4 is completely in sync (0/0)
  OK - partition 5 is completely in sync (0/0)
  OK - partition 6 is completely in sync (0/0)
  OK - partition 7 is completely in sync (0/0)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Output can be formatted for consumption by Telegraf

  $ check --telegraf | python -m json.tool
  [
      {
          "available": 1,
          "lag_time": 0.0,
          "offset": 1,
          "partition": 0
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 1
      },
      {
          "available": 1,
          "lag_time": 0.0,
          "offset": 1,
          "partition": 2
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 3
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 4
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 5
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 6
      },
      {
          "available": 0,
          "lag_time": 0.0,
          "offset": 0,
          "partition": 7
      }
  ]

Cleanup

  $ hgmo clean
