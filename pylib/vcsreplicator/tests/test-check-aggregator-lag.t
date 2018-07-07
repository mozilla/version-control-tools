#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ alias check='hgmo exec hgssh /var/hg/venv_tools/bin/check_vcsreplicator_aggregator_lag /etc/mercurial/pushdataaggregator-pending.ini'

Check should be OK by default

  $ hgmo exec hgssh /usr/lib64/nagios/plugins/custom/check_kafka_hg_heartbeat
  OK - heartbeat message sent to 8/8 partitions successfully

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ sleep 2

  $ check
  OK - aggregator has copied all fully replicated messages
  
  OK - partition 0 is completely in sync (1/1)
  OK - partition 1 is completely in sync (1/1)
  OK - partition 2 is completely in sync (1/1)
  OK - partition 3 is completely in sync (1/1)
  OK - partition 4 is completely in sync (1/1)
  OK - partition 5 is completely in sync (1/1)
  OK - partition 6 is completely in sync (1/1)
  OK - partition 7 is completely in sync (1/1)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Stop the aggregator so there is message lag

  $ hgmo exec hgssh /usr/bin/supervisorctl stop pushdataaggregator-pending
  pushdataaggregator-pending: stopped

No issues reported when thresholds aren't met

  $ hgmo create-repo repo0 scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ check
  OK - 2 messages from 2 partitions behind
  
  OK - partition 0 is 1 messages behind (1/2)
  OK - partition 1 is completely in sync (1/1)
  OK - partition 2 is 1 messages behind (1/2)
  OK - partition 3 is completely in sync (1/1)
  OK - partition 4 is completely in sync (1/1)
  OK - partition 5 is completely in sync (1/1)
  OK - partition 6 is completely in sync (1/1)
  OK - partition 7 is completely in sync (1/1)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Warning reported when message count hits threshold

  $ check --warning-count 1
  WARNING - 2 messages from 2 partitions behind
  
  WARNING - partition 0 is 1 messages behind (1/2)
  OK - partition 1 is completely in sync (1/1)
  WARNING - partition 2 is 1 messages behind (1/2)
  OK - partition 3 is completely in sync (1/1)
  OK - partition 4 is completely in sync (1/1)
  OK - partition 5 is completely in sync (1/1)
  OK - partition 6 is completely in sync (1/1)
  OK - partition 7 is completely in sync (1/1)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [1]

Critical reported when message count hits threshold

  $ check --critical-count 1
  CRITICAL - 2 messages from 2 partitions behind
  
  CRITICAL - partition 0 is 1 messages behind (1/2)
  OK - partition 1 is completely in sync (1/1)
  CRITICAL - partition 2 is 1 messages behind (1/2)
  OK - partition 3 is completely in sync (1/1)
  OK - partition 4 is completely in sync (1/1)
  OK - partition 5 is completely in sync (1/1)
  OK - partition 6 is completely in sync (1/1)
  OK - partition 7 is completely in sync (1/1)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.
  [2]

Resuming aggregator clears check

  $ hgmo exec hgssh /usr/bin/supervisorctl start pushdataaggregator-pending
  pushdataaggregator-pending: started

  $ check --warning-count 0
  OK - aggregator has copied all fully replicated messages
  
  OK - partition 0 is completely in sync (2/2)
  OK - partition 1 is completely in sync (1/1)
  OK - partition 2 is completely in sync (2/2)
  OK - partition 3 is completely in sync (1/1)
  OK - partition 4 is completely in sync (1/1)
  OK - partition 5 is completely in sync (1/1)
  OK - partition 6 is completely in sync (1/1)
  OK - partition 7 is completely in sync (1/1)
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmo/ops.html
  for details about this check.

Cleanup

  $ hgmo clean
