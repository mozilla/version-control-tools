  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > vcsreplicator = $TESTDIR/pylib/vcsreplicator/vcsreplicator/hgext.py
  > EOF

No config with extension installed should cause immediate abort

  $ hg st
  abort: replication.role config option not set
  [255]

Invalid replication.role results in error

  $ hg --config replication.role=invalid st
  abort: unsupported value for replication.role: invalid
  (expected "producer" or "consumer")
  [255]

  $ cat >> .hg/hgrc << EOF
  > [replication]
  > role = producer
  > EOF

Missing hosts

  $ hg st
  abort: replicationproducer.hosts config option not set
  [255]

Missing clientid

  $ cat >> .hg/hgrc << EOF
  > [replicationproducer]
  > hosts = dummy1,dummy2
  > EOF

  $ hg st
  abort: replicationproducer.clientid config option not set
  [255]

Missing topic

  $ cat >> .hg/hgrc << EOF
  > clientid = 1
  > EOF

  $ hg st
  abort: replicationproducer.topic config option not set
  [255]

No partition

  $ cat >> .hg/hgrc << EOF
  > topic = topic
  > EOF

  $ hg st
  abort: replicationproducer.partition config option not set
  [255]

Non-integer partition

  $ cat >> .hg/hgrc << EOF
  > partition = foobar
  > EOF

  $ hg st
  abort: replicationproducer.partition is not an integer ('foobar')
  [255]

No reqacks

  $ cat >> .hg/hgrc << EOF
  > partition = 1
  > EOF

  $ hg st
  abort: replicationproducer.reqacks must be set to -1, 0, or 1
  [255]

Bad reqacks value

  $ cat >> .hg/hgrc << EOF
  > reqacks = 2
  > EOF

  $ hg st
  abort: replicationproducer.reqacks must be set to -1, 0, or 1
  [255]

No acktimeout

  $ cat >> .hg/hgrc << EOF
  > reqacks = -1
  > EOF

  $ hg st
  abort: replicationproducer.acktimeout config option not set
  [255]

No error expected

  $ cat >> .hg/hgrc << EOF
  > acktimeout = 5000
  > EOF

  $ hg st
