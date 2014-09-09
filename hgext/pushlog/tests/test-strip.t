  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ export USER=hguser

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
  $ echo foo2 > foo
  $ hg commit -m 'second'
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

Stripping changesets should result in pushlog getting stripped

  $ cd ../server
  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  $ hg --config extensions.mq= strip -r 1 --no-backup

  $ hg log
  changeset:   0:96ee1d7354c4
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial
  
TODO pushlog doesn't handle stripping yet, so this output is wrong. It
should only contain push #1 or a dummy value for push #2, depending on
how it is implemented.
  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
