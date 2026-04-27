Tests for the client-side error, retry, and rollback paths in
`exchangepullpushlog`. A server-side test extension
(`brokenpushlogstream`) replaces the `pushlog-stream` command with a
version whose behaviour is selected by a file on disk.

  $ . $TESTDIR/hghooks/tests/common.sh

  $ export USER=hguser

Set up the server. We load `pushlog` first, then the broken override.

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > brokenpushlogstream = $TESTDIR/hgext/pushlog/tests/brokenpushlogstream.py
  > EOF
  $ cd ..

Populate the server with two pushes so the stream has something to
emit (and something to partially emit for the "after-one" case).

  $ hg init client-seed
  $ cd client-seed
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ echo foo2 > foo
  $ hg commit -m 'second'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ cd ..

  $ cd server
  $ hg serve -d -p $HGPORT --pid-file server.pid -E error.log -A access.log
  $ cat server.pid >> $DAEMON_PIDS
  $ cd ..

Baseline: with no fail mode set, pull completes and records both
pushes locally.

  $ hg init client-baseline
  $ cd client-baseline
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT --config pushlog.retrydelayms=0
  pulling from http://$LOCALHOST:$HGPORT/
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 pushes
  added 2 changesets with 2 changes to 1 files
  new changesets 96ee1d7354c4:d0fddd3a3fb5
  (run 'hg update' to get a working copy)
  $ dumppushlog client-baseline
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  $ cd ..

Fail mode: always-error. Server returns `error` trailer immediately on
every request. Client should warn three times and abort.

  $ echo always-error > server/.hg/pushlog-stream-fail-mode
  $ hg init client-always-error
  $ cd client-always-error
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT --config pushlog.retrydelayms=0
  pulling from http://$LOCALHOST:$HGPORT/
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  remote error fetching pushlog on attempt 1: simulated server error
  remote error fetching pushlog on attempt 2: simulated server error
  remote error fetching pushlog on attempt 3: simulated server error
  transaction abort!
  rolling back pushlog
  rollback completed
  abort: remote error fetching pushlog after 3 attempts
  [255]

After the abort, the whole pull transaction rolled back — the
pushlog db file was created as part of opening the connection but
has no rows, so `dumppushlog` produces no output.

  $ dumppushlog client-always-error
  $ cd ..

Fail mode: always-truncate. Server yields one data row and then closes
without a trailer. Client should detect the missing trailer and retry.

  $ echo always-truncate > server/.hg/pushlog-stream-fail-mode
  $ hg init client-always-truncate
  $ cd client-always-truncate
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT --config pushlog.retrydelayms=0
  pulling from http://$LOCALHOST:$HGPORT/
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  remote error fetching pushlog on attempt 1: stream ended without trailer
  remote error fetching pushlog on attempt 2: stream ended without trailer
  remote error fetching pushlog on attempt 3: stream ended without trailer
  transaction abort!
  rolling back pushlog
  rollback completed
  abort: remote error fetching pushlog after 3 attempts
  [255]
  $ cd ..

Fail mode: always-error-after-one. Server streams one data row, then
emits an `error` trailer. The client should insert the row, see the
trailer, roll the row back, and retry. On attempt 3 the same thing
happens and the pull aborts — so no pushlog should exist locally.

  $ echo always-error-after-one > server/.hg/pushlog-stream-fail-mode
  $ hg init client-error-after-one
  $ cd client-error-after-one
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT --config pushlog.retrydelayms=0
  pulling from http://$LOCALHOST:$HGPORT/
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  remote error fetching pushlog on attempt 1: simulated error after one row
  remote error fetching pushlog on attempt 2: simulated error after one row
  remote error fetching pushlog on attempt 3: simulated error after one row
  transaction abort!
  rolling back pushlog
  rollback completed
  abort: remote error fetching pushlog after 3 attempts
  [255]
  $ dumppushlog client-error-after-one
  $ cd ..

Recovery: after clearing the fail mode, a fresh client pulls
successfully.

  $ rm server/.hg/pushlog-stream-fail-mode
  $ hg init client-recovered
  $ cd client-recovered
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ hg pull http://localhost:$HGPORT --config pushlog.retrydelayms=0
  pulling from http://$LOCALHOST:$HGPORT/
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 pushes
  added 2 changesets with 2 changes to 1 files
  new changesets 96ee1d7354c4:d0fddd3a3fb5
  (run 'hg update' to get a working copy)
  $ dumppushlog client-recovered
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  $ cd ..

Confirm no errors in log.

  $ cat ./server/error.log
