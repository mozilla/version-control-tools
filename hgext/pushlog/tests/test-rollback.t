  $ . $TESTDIR/hghooks/tests/common.sh
  $ export USER=hguser
  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF

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
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

A failure during the transaction should cause the pushlog to not
record

  $ echo foo2 > foo
  $ hg commit -m 'second'
  $ cat >> ../server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.abort = /bin/echo 'fake hook failure' && exit 1
  > priority.pretxnchangegroup.abort = -100
  > EOF

  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.
  fake hook failure
  rolling back pushlog
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.abort hook exited with status 1
  [255]

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)

Remove the abort hook and ensure pushing again works as expected

  $ cat >> ../server/.hg/hgrc << EOF
  > pretxnchangegroup.abort = /bin/echo 'fake hook success' && exit 0
  > EOF
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.
  fake hook success

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
