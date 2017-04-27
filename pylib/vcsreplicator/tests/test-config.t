#require vcsreplicator

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > vcsreplicator = $TESTDIR/pylib/vcsreplicator/vcsreplicator/hgext.py
  > EOF

No config with extension installed should cause immediate abort

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

No partition map

  $ cat >> .hg/hgrc << EOF
  > topic = topic
  > EOF

  $ hg st
  abort: replicationproducer.partitionmap.* config options not set
  [255]

No reqacks

  $ cat >> .hg/hgrc << EOF
  > partitionmap.0 = 0:.*
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
