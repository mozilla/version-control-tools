#require vcsreplicator

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > vcsreplicator = $TESTDIR/pylib/vcsreplicator/vcsreplicator/hgext.py
  > EOF

No config with extension installed should cause immediate abort

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.hosts config option not set') (glob) (?)
  *Abort: replicationproducer.hosts config option not set (glob) (?)
      raise error.Abort(b"replicationproducer.hosts config option not set")
  *Abort: replicationproducer.hosts config option not set (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.hosts config option not set

Missing clientid

  $ cat >> .hg/hgrc << EOF
  > [replicationproducer]
  > hosts = dummy1,dummy2
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.clientid config option not set') (glob) (?)
  *Abort: replicationproducer.clientid config option not set (glob) (?)
      raise error.Abort(b"replicationproducer.clientid config option not set")
  *Abort: replicationproducer.clientid config option not set (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.clientid config option not set

Missing topic

  $ cat >> .hg/hgrc << EOF
  > clientid = 1
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.topic config option not set') (glob) (?)
  *Abort: replicationproducer.topic config option not set (glob) (?)
      raise error.Abort(b"replicationproducer.topic config option not set")
  *Abort: replicationproducer.topic config option not set (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.topic config option not set

No partition map

  $ cat >> .hg/hgrc << EOF
  > topic = topic
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.partitionmap.* (glob) (?)
  *Abort: replicationproducer.partitionmap.* config options not set (glob) (?)
      b"replicationproducer.partitionmap.* config options not set"
  *Abort: replicationproducer.partitionmap.* config options not set (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.partitionmap.* config options not set

No reqacks

  $ cat >> .hg/hgrc << EOF
  > partitionmap.0 = 0:.*
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.reqacks must be set to -1,* (glob) (?)
  *Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (glob) (?)
      raise error.Abort(b"replicationproducer.reqacks must be set to -1, 0, or 1")
  *Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.reqacks must be set to -1, 0, or 1

Bad reqacks value

  $ cat >> .hg/hgrc << EOF
  > reqacks = 2
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.reqacks must be set to -1,* (glob) (?)
  *Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (glob) (?)
      raise error.Abort(b"replicationproducer.reqacks must be set to -1, 0, or 1")
  *Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.reqacks must be set to -1, 0, or 1

No acktimeout

  $ cat >> .hg/hgrc << EOF
  > reqacks = -1
  > EOF

  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.acktimeout config option* (glob) (?)
  *Abort: replicationproducer.acktimeout config option not set (glob) (?)
      raise error.Abort(b"replicationproducer.acktimeout config option not set")
  *Abort: replicationproducer.acktimeout config option not set (glob)
  *** failed to set up extension vcsreplicator: replicationproducer.acktimeout config option not set

No error expected

  $ cat >> .hg/hgrc << EOF
  > acktimeout = 5000
  > EOF

  $ hg st
