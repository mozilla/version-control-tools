  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ configurereleasinghooks server
  $ cd server

  $ echo "foo" > dummy
  $ hg commit -A -m 'original repo commit; r=baku'
  adding dummy

  $ cd ..
  $ hg clone server client
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip=
  > EOF

Editing the sync-messages.ini file without any review should fail

  $ mkdir -p ipc/ipdl
  $ echo "foo" > ipc/ipdl/sync-messages.ini
  $ hg add ipc/ipdl/sync-messages.ini
  $ hg commit -m 'Bug 123 - Add sync-messages.ini'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************** ERROR *********************************
  Changeset 8fb3e82ba334 alters sync-messages.ini without IPC peer review.
  
  Please, request review from either:
    - Andrew McCreight (:mccr8)
    - Jed Davis (:jld)
    - Nika Layzell (:nika)
    - David Parks (:handyman)
  ************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Editing the sync-messages.ini file without /IPC/ peer review should fail

  $ hg -q commit --amend -m 'Bug 123 - Add Bar; r=foobar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************** ERROR *********************************
  Changeset d970a5c85d15 alters sync-messages.ini without IPC peer review.
  
  Please, request review from either:
    - Andrew McCreight (:mccr8)
    - Jed Davis (:jld)
    - Nika Layzell (:nika)
    - David Parks (:handyman)
  ************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Editing the `sync-message.ini` file without IPC peer but with `scm_allow_direct_push`
ownership should pass.

  $ echo "scm_allow_direct_push" > $TESTTMP/server/.hg/moz-owner
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Editing the sync-messages.ini file with /IPC/ peer review should pass

  $ echo "bar" > ipc/ipdl/sync-messages.ini
  $ hg -q commit -m 'Bug 123 - Add Bar; r=jld'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
