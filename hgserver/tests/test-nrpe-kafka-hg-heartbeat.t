#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ hgmo exec hgssh /activate-vcsreplicator --global
  activated vcsreplicator globally

  $ alias check='hgmo exec hgssh /usr/lib64/nagios/plugins/custom/check_kafka_hg_heartbeat'

Check should pass by default

  $ check
  OK - heartbeat message sent successfully
  
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

Check should still pass with a node out of the cluster

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  OK - heartbeat message sent successfully
  
  sending heartbeat to partition 0
  sending heartbeat to partition 1
  sending heartbeat to partition 2
  sending heartbeat to partition 3
  sending heartbeat to partition 4
  sending heartbeat to partition 5
  sending heartbeat to partition 6
  sending heartbeat to partition 7
  wrote heartbeat message into 8 partitions

Check should fail with no quorum in cluster

  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  CRITICAL - error sending heartbeat
  
  sending heartbeat to partition 0
  abort: error sending heartbeat: UNKNOWN
  
  Unable to write message into replication log. This likely 
  means incoming pushes will be denied since they will unable to 
  be replicated.
  [2]

  $ hgmo stop
