#require vcsreplicator

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > vcsreplicator = $TESTDIR/pylib/vcsreplicator/vcsreplicator/hgext.py
  > EOF

No config with extension installed should cause immediate abort

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.hosts config option not set') (glob) (?)
  Abort: replicationproducer.hosts config option not set (?)
  *** failed to set up extension vcsreplicator: replicationproducer.hosts config option not set
#else
  $ hg st
  abort: replicationproducer.hosts config option not set
  [255]
#endif

Missing clientid

  $ cat >> .hg/hgrc << EOF
  > [replicationproducer]
  > hosts = dummy1,dummy2
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.clientid config option not set') (glob) (?)
  Abort: replicationproducer.clientid config option not set (?)
  *** failed to set up extension vcsreplicator: replicationproducer.clientid config option not set
#else
  $ hg st
  abort: replicationproducer.clientid config option not set
  [255]
#endif

Missing topic

  $ cat >> .hg/hgrc << EOF
  > clientid = 1
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.topic config option not set') (glob) (?)
  Abort: replicationproducer.topic config option not set (?)
  *** failed to set up extension vcsreplicator: replicationproducer.topic config option not set
#else
  $ hg st
  abort: replicationproducer.topic config option not set
  [255]
#endif

No partition map

  $ cat >> .hg/hgrc << EOF
  > topic = topic
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.partitionmap.* (glob) (?)
  Abort: replicationproducer.partitionmap.* config options not set (?)
  *** failed to set up extension vcsreplicator: replicationproducer.partitionmap.* config options not set
#else
  $ hg st
  abort: replicationproducer.partitionmap.* config options not set
  [255]
#endif

No reqacks

  $ cat >> .hg/hgrc << EOF
  > partitionmap.0 = 0:.*
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.reqacks must be set to -1,* (glob) (?)
  Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (?)
  *** failed to set up extension vcsreplicator: replicationproducer.reqacks must be set to -1, 0, or 1
#else
  $ hg st
  abort: replicationproducer.reqacks must be set to -1, 0, or 1
  [255]
#endif

Bad reqacks value

  $ cat >> .hg/hgrc << EOF
  > reqacks = 2
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.reqacks must be set to -1,* (glob) (?)
  Abort: replicationproducer.reqacks must be set to -1, 0, or 1 (?)
  *** failed to set up extension vcsreplicator: replicationproducer.reqacks must be set to -1, 0, or 1
#else
  $ hg st
  abort: replicationproducer.reqacks must be set to -1, 0, or 1
  [255]
#endif

No acktimeout

  $ cat >> .hg/hgrc << EOF
  > reqacks = -1
  > EOF

#if hg43
  $ hg st
  Traceback (most recent call last): (?)
    File "* (glob) (?)
      uisetup(ui) (?)
    File "* (glob) (?)
      raise *.Abort('replicationproducer.acktimeout config option* (glob) (?)
  Abort: replicationproducer.acktimeout config option not set (?)
  *** failed to set up extension vcsreplicator: replicationproducer.acktimeout config option not set
#else
  $ hg st
  abort: replicationproducer.acktimeout config option not set
  [255]
#endif

No error expected

  $ cat >> .hg/hgrc << EOF
  > acktimeout = 5000
  > EOF

  $ hg st
