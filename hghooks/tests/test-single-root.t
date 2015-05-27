  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.single_root = python:mozhghooks.single_root.hook
  > EOF

Pushing to an empty repository works

  $ hg init client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Pushing additional commits works

  $ echo r1c1 > foo
  $ hg commit -m 'root 1 commit 1'
  $ echo r1c2 > foo
  $ hg commit -m 'root 1 commit 2'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

Create a new root

  $ hg up -r null
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo r2 > bar
  $ hg commit -A -m 'root 2 commit 1'
  adding bar
  created new head

Pushing new root should be rejected

  $ hg push -f ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  *** pushing unrelated repository ***
  
  Changeset 383834333835 introduces a new root changeset into this repository. This
  almost certainly means you accidentally force pushed to the wrong
  repository and/or URL.
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.single_root hook failed
  [255]

  $ hg --config extensions.strip= strip -r tip
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/884385885a43-b8fe5de7-backup.hg (glob)
  $ hg up tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Pushing new root as part of multiple commits will be rejected

  $ echo r1c3 > foo
  $ hg commit -m 'root 1 commit 3'
  $ hg up -r null
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo r2 > bar
  $ hg commit -A -m 'root 3 commit 1'
  adding bar
  created new head
  $ hg push -f ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  *** pushing unrelated repository ***
  
  Changeset 343130316639 introduces a new root changeset into this repository. This
  almost certainly means you accidentally force pushed to the wrong
  repository and/or URL.
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.single_root hook failed
  [255]
