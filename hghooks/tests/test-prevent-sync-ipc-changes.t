  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO
  $ cd server

  $ echo "foo" > dummy
  $ hg commit -A -m 'original repo commit; r=baku'
  adding dummy

  $ cd ..
  $ hg clone server client
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
mq provides `hg strip` for older Mercurial versions and supplies it even
in modern versions
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
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
  added 1 changesets with 1 changes to 1 files
  
  ******************************** ERROR *********************************
  Changeset 8fb3e82ba334 alters sync-messages.ini without IPC peer review.
  
  Please, request review from either:
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Bill McCloskey (:billm)
    - David Anderson (:dvander)
    - Jed David (:jld)
    - Kan-Ru Chen (:kanru)
    - Nathan Froyd (:froydnj)
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
  added 1 changesets with 1 changes to 1 files
  
  ******************************** ERROR *********************************
  Changeset d970a5c85d15 alters sync-messages.ini without IPC peer review.
  
  Please, request review from either:
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Bill McCloskey (:billm)
    - David Anderson (:dvander)
    - Jed David (:jld)
    - Kan-Ru Chen (:kanru)
    - Nathan Froyd (:froydnj)
  ************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Editing the sync-messages.ini file with /IPC/ peer review should pass

  $ hg -q commit --amend -m 'Bug 123 - Add Bar; r=billm'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
