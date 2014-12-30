  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > 
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF

  $ export USER=hguser
  $ hg init server
  $ cd server
  $ hg serve -d -p $HGPORT --pid-file server.pid -E error.log -A access.log
  $ cat server.pid >> $DAEMON_PIDS
  $ cd ..

Lack of permissions to create pushlog file should not impact read-only operations

  $ chmod u-w server/.hg
  $ chmod g-w server/.hg

  $ hg clone ssh://user@dummy/$TESTTMP/server clone
  no changes found
  added 0 pushes
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Seed the pushlog for our next test

  $ chmod u+w server/.hg
  $ chmod g+w server/.hg

  $ cd clone
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.

Lack of permissions on pushlog should prevent pushes from completing

  $ chmod 444 ../server/.hg/pushlog2.db
  $ echo perms > foo
  $ hg commit -m 'bad permissions'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Error inserting into pushlog. Please retry your push.
  remote: rolling back pushlog
  remote: transaction abort!
  remote: rollback completed
  remote: abort: pretxnchangegroup.pushlog hook failed
  [1]
