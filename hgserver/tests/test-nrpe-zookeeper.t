#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ hgmo exec hgssh /activate-vcsreplicator --global
  activated vcsreplicator globally

check_zookeeper without any arguments will error

  $ alias check_zk='hgmo exec hgssh /repo/hg/version-control-tools/scripts/check_zookeeper'

  $ check_zk
  ERROR: must specify -H or -c
  [2]

Should error connecting to non-listening port

  $ check_zk -H localhost:2182
  socket error connecting to localhost: [Errno 111] Connection refused
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.
  [2]

Should be OK checking node itself

  $ check_zk -H localhost:2181
  zookeeper node OK
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.

Cluster should be healthy

  $ check_zk -c /etc/zookeeper/zoo.cfg
  zookeeper ensemble OK
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.

Node and cluster report as healthy

  $ check_zk -H localhost:2181 -c /etc/zookeeper/zoo.cfg
  zookeeper node and ensemble OK
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.

Stopping us should result in failure

  $ hgmo exec hgssh /usr/bin/supervisorctl stop zookeeper
  zookeeper: stopped
  $ check_zk -H localhost:2181
  socket error connecting to localhost: [Errno 111] Connection refused
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.
  [2]

The cluster should report warning state

  $ check_zk -c /etc/zookeeper/zoo.cfg
  ENSEMBLE WARNING - only have 1/2 expected followers
  ENSEMBLE WARNING - socket error connecting to *: [Errno 111] Connection refused (glob)
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.
  [1]

Ensemble state should recover when zookeeper started

  $ hgmo exec hgssh /usr/bin/supervisorctl start zookeeper
  zookeeper: started
  $ check_zk -c /etc/zookeeper/zoo.cfg
  zookeeper ensemble OK
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.

Stopping a separate node should result in warning

  $ hgmo exec hgweb0 /usr/bin/supervisorctl stop zookeeper
  zookeeper: stopped
  $ check_zk -c /etc/zookeeper/zoo.cfg
  ENSEMBLE WARNING - only have 1/2 expected followers
  ENSEMBLE WARNING - socket error connecting to *: [Errno 111] Connection refused (glob)
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.
  [1]

Stopping multiple nodes should result in loss of quorum

  $ hgmo exec hgweb1 /usr/bin/supervisorctl stop zookeeper
  zookeeper: stopped
  $ check_zk -c /etc/zookeeper/zoo.cfg
  ENSEMBLE CRITICAL - unable to find leader node; ensemble likely not writable
  ENSEMBLE WARNING - node (*) is alive but not available (glob)
  ENSEMBLE WARNING - socket error connecting to *: [Errno 111] Connection refused (glob)
  ENSEMBLE WARNING - socket error connecting to *: [Errno 111] Connection refused (glob)
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmo/ops.html
  for more info on monitor and alerts.
  [2]

  $ hgmo clean
