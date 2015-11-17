#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 3
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
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central (glob)
  * vcsreplicator.consumer received signal 15 (glob)
  * vcsreplicator.consumer exiting gracefully (glob)
  * kafka.conn Unable to receive data from Kafka (glob)
  Traceback (most recent call last):
    File "/repo/hg/venv_replication/lib/python2.7/site-packages/kafka/conn.py", line 97, in _read_bytes
      data = self._sock.recv(min(bytes_left, 4096))
  error: [Errno 4] Interrupted system call
  * kafka.client ConnectionError attempting to receive a response to request * from server BrokerMetadata(nodeId=*, host='*', port=*): Kafka @ * went away (glob)
  * kafka.consumer.simple FailedPayloadsError for pushdata:2 (glob)
  * vcsreplicator.consumer exiting from main consume loop (glob)
  * vcsreplicator.consumer process exiting gracefully (glob)

Send a message to the replication system

  $ hgmo exec hgssh /activate-hook mozilla-central dummy value
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

Start consumer daemon and verify it picks up where it left off

  $ hgmo exec hgweb0 /usr/bin/supervisorctl start vcsreplicator:2
  vcsreplicator:2: started

  $ sleep 1
  $ hgmo exec hgweb0 tail -n 3 /var/log/vcsreplicator/consumer.log
  * vcsreplicator.consumer process exiting gracefully (glob)
  * vcsreplicator.consumer starting consumer for topic=pushdata group=* partitions=[*] (glob)
  * vcsreplicator.consumer writing hgrc: /repo/hg/mozilla/mozilla-central/.hg/hgrc (glob)

Cleanup

  $ hgmo stop
