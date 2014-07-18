  $ hg init server
  $ cd server
  $ touch foo
  $ hg commit -A -m 'add foo'
  adding foo

  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Clone without bundle support on server should fall back to normal

  $ hg --debug --config extensions.bundleclone=$TESTDIR/hgext/bundleclone clone http://localhost:$HGPORT client1 | grep 'bundle clone not supported'
  bundle clone not supported
  $ ls client1
  foo

Clone with bundle support but requested heads will not use bundles

  $ cat >> server/.hg/hgrc << EOF
  > [extensions]
  > bundleclone = $TESTDIR/hgext/bundleclone
  > EOF
  $ hg -R server serve -d -p $HGPORT1 --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ hg --debug --config extensions.bundleclone=$TESTDIR/hgext/bundleclone clone -r 53245c60e68 http://localhost:$HGPORT1 client2 | grep 'cannot perform bundle clone if heads requested'
  cannot perform bundle clone if heads requested
