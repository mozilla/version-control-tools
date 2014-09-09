  $ . $TESTDIR/hghooks/tests/common.sh
  $ export USER=hguser
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ cd client

Single valid pushlog verifies OK

  $ touch foo
  $ hg -q commit -A -m 'initial'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Inserted into the pushlog db successfully.

  $ echo second > foo
  $ hg commit -m 'second'
  $ echo third > foo
  $ hg commit -m 'third'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  Trying to insert into pushlog.
  Inserted into the pushlog db successfully.

  $ hg -R ../server verifypushlog
  pushlog contains all 3 changesets across 2 pushes

Add a node to the pushlog that doesn't exist

  $ cp ../server/.hg/pushlog2.db ../server/.hg/pushlog2.db.good
  $ sqlite3 ../server/.hg/pushlog2.db "INSERT INTO changesets (pushid, rev, node) VALUES (1, 3, 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef')"

  $ hg -R ../server verifypushlog
  changeset in pushlog entry #1 does not exist: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef
  pushlog has errors
  [1]
  $ mv ../server/.hg/pushlog2.db.good ../server/.hg/pushlog2.db

Changeset in repo without pushlog entry should trigger an error

  $ sqlite3 ../server/.hg/pushlog2.db "DELETE FROM changesets WHERE pushid=2"
  $ hg -R ../server verifypushlog
  pushlog entry has no nodes: #2
  changeset does not exist in pushlog: 75f01efc4bb4419cbc86560aa69b579e45bfbf97
  changeset does not exist in pushlog: 182f8e2b4b5e4cc72d4a3e5cbaf78e67a0264a7e
  pushlog has errors
  [1]
