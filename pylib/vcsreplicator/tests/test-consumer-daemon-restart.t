#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)

Gracefully shut down a consumer daemon

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop vcsreplicator:2
  vcsreplicator:2: stopped

  $ hgmo exec hgweb0 cat /var/log/vcsreplicator/consumer.log
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  No handlers could be found for logger "kafka.conn"
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer received signal 15
  vcsreplicator.consumer exiting gracefully
  kafka.conn Unable to receive data from Kafka
  Traceback (most recent call last):
    File "/var/hg/venv_replication/lib/python2.7/site-packages/kafka/conn.py", line 97, in _read_bytes
      data = self._sock.recv(min(bytes_left, 4096))
  error: [Errno 4] Interrupted system call
  kafka.client ConnectionError attempting to receive a response to request * from server BrokerMetadata(nodeId=*, host='*', port=9092): Kafka @ *:9092 went away (glob)
  kafka.consumer.simple FailedPayloadsError for pushdata:2
  vcsreplicator.consumer exiting from main consume loop
  vcsreplicator.consumer process exiting gracefully

Send a message to the replication system

  $ hgmo exec hgssh /set-hgrc-option mozilla-central hooks dummy value
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

Start consumer daemon and verify it picks up where it left off

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start vcsreplicator:2
  vcsreplicator:2: started

  $ sleep 1
  $ hgmo exec hgweb0 tail -n 3 /var/log/vcsreplicator/consumer.log
  vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[2] (glob)
  vcsreplicator.consumer processing hg-hgrc-update-1 from partition 2 offset 1
  vcsreplicator.consumer writing hgrc: /repo/hg/mozilla/mozilla-central/.hg/hgrc

Cleanup

  $ hgmo clean
