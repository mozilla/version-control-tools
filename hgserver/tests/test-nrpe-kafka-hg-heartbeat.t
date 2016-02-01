#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ alias check='hgmo exec hgssh /usr/lib64/nagios/plugins/custom/check_kafka_hg_heartbeat'

Check should pass by default

  $ check
  OK - heartbeat message sent to 8/8 partitions successfully

Check should still pass with a node out of the cluster

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  OK - heartbeat message sent to 8/8 partitions successfully

Check should fail with no quorum in cluster

  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop kafka
  kafka: stopped
  $ check
  CRITICAL - error writing to partition 0 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=0, error=19, offset=-1)
  CRITICAL - error writing to partition 1 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=1, error=19, offset=-1)
  CRITICAL - error writing to partition 2 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=2, error=19, offset=-1)
  CRITICAL - error writing to partition 3 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=3, error=19, offset=-1)
  CRITICAL - error writing to partition 4 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=4, error=19, offset=-1)
  CRITICAL - error writing to partition 5 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=5, error=19, offset=-1)
  CRITICAL - error writing to partition 6 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=6, error=19, offset=-1)
  CRITICAL - error writing to partition 7 (leader: $DOCKER_HOSTNAME): UNKNOWN
  ProduceResponse(topic='pushdata', partition=7, error=19, offset=-1)
  We were unable to write a heartbeat message into the replication
  log. This likely means incoming pushes will not complete since they
  will not be able to write to the replication log.
  
  Please report this failure to #vcs or notify oncall ASAP.
  [2]

  $ hgmo clean
