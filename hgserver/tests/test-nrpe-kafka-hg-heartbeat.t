#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ hgmo exec hgssh /activate-vcsreplicator --global
  activated vcsreplicator globally

  $ alias check='hgmo exec hgssh /usr/lib64/nagios/plugins/custom/check_kafka_hg_heartbeat'

Check should pass by default

  $ check
  OK - wrote heartbeat message into replication log

Check should still pass with a node out of the cluster

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  OK - wrote heartbeat message into replication log

Check should fail with no quorum in cluster

  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  CRITICAL - abort: error sending heartbeat: UNKNOWN
  
  Unable to write message into replication log. This likely 
  means incoming pushes will be denied since they will unable to 
  be replicated.
  [2]

  $ hgmo stop
