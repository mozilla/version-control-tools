  $ . $TESTDIR/hghooks/tests/common.sh

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > EOF

  $ export USER=hguser
  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg serve -d -p $HGPORT --pid-file server.pid -E error.log -A access.log
  $ cat server.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg init client
  $ cd client
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog

Pulling from a remote that has pushlog will fetch pushlog data

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT
  pulling from http://localhost:$HGPORT/
  searching for changes
  no changes found
  added 1 pushes

  $ dumppushlog client
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)

  $ cd ..
  $ hg -q clone http://localhost:$HGPORT client2
  $ cd client2
  $ echo foo2 > foo
  $ hg commit -m 'second'
  $ hg -q push ../server
  recorded push in pushlog
  $ echo foo3 > foo
  $ hg commit -m 'third'
  $ echo foo4 > foo
  $ hg commit -m 'fourth'
  $ hg -q push ../server
  recorded push in pushlog
  $ cd ..

  $ cd client
  $ hg pull http://localhost:$HGPORT
  pulling from http://localhost:$HGPORT/
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  (not updating pushlog since changesets come from pull)
  added 2 pushes
  (run 'hg update' to get a working copy)
  $ dumppushlog client
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 53532d3f0b038c6e7bf435c45f28c1be1ab97049 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 3; Node: 77a9042f9fafe759713d8e76d027e55fee784512 (re)

  $ cd ..

Cloning from scratch will retrieve multiple pushlog entries

  $ hg -q --config extensions.pushlog=$TESTDIR/hgext/pushlog clone http://localhost:$HGPORT clone-multiple
  $ dumppushlog clone-multiple
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 53532d3f0b038c6e7bf435c45f28c1be1ab97049 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 3; Node: 77a9042f9fafe759713d8e76d027e55fee784512 (re)

Cloning over SSH will fetch pushlog data

  $ hg -q --config extensions.pushlog=$TESTDIR/hgext/pushlog clone ssh://user@dummy/$TESTTMP/server clone-ssh
  $ dumppushlog clone-ssh
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 53532d3f0b038c6e7bf435c45f28c1be1ab97049 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 3; Node: 77a9042f9fafe759713d8e76d027e55fee784512 (re)

Incremental pushlog fetch works over SSH

  $ cd client2
  $ echo ssh-incremental > foo
  $ hg commit -m 'ssh-incremental'
  $ hg -q push ../server
  recorded push in pushlog

  $ cd ../clone-ssh
  $ hg --config extensions.pushlog=$TESTDIR/hgext/pushlog pull
  pulling from ssh://user@dummy/$TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (not updating pushlog since changesets come from pull)
  added 1 pushes
  (run 'hg update' to get a working copy)

  $ dumppushlog clone-ssh
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 53532d3f0b038c6e7bf435c45f28c1be1ab97049 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 3; Node: 77a9042f9fafe759713d8e76d027e55fee784512 (re)
  ID: 4; user: hguser; Date: \d+; Rev: 4; Node: f77647c7d4e3e4728ad0de09ffd09f8cf5a160a1 (re)

Pulling an old changeset only pulls relevant changesets

  $ cd ../client2
  $ echo pull-old1 > foo
  $ hg commit -m 'pull old 1'
  $ hg -q push ../server
  recorded push in pushlog
  $ echo pull-old2 > foo
  $ hg commit -m 'pull old 2'
  $ hg -q push ../server
  recorded push in pushlog

  $ cd ../clone-ssh
  $ hg --config extensions.pushlog=$TESTDIR/hgext/pushlog pull -r 1a68e4eb4da6
  pulling from ssh://user@dummy/$TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (not updating pushlog since changesets come from pull)
  transaction abort!
  rollback completed
  abort: unknown revision '2e70e96c7d550e541406a47d87df354309fe9a72'!
  [255]

  $ cd ..
