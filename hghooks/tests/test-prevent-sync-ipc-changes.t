  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_webidl = python:mozhghooks.prevent_webidl_changes.hook
  > EOF

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
  
  
  ************************** ERROR ****************************
  
  sync-messages.ini altered in changeset 8fb3e82ba334 without IPC peer review
  
  
  Changes to sync-messages.ini in this repo require review from a IPC peer in the form of r=...
  This is to ensure that we behave responsibly by not adding sync IPC messages that cause performance issues needlessly. We appreciate your understanding..
  
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_webidl hook failed
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
  
  
  ************************** ERROR ****************************
  
  sync-messages.ini altered in changeset d970a5c85d15 without IPC peer review
  
  
  Changes to sync-messages.ini in this repo require review from a IPC peer in the form of r=...
  This is to ensure that we behave responsibly by not adding sync IPC messages that cause performance issues needlessly. We appreciate your understanding..
  
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_webidl hook failed
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
  You've received proper review from an IPC peer on the sync-messages.ini change(s) in commit 62716423067e, thanks for paying enough attention.
