  $ cat >> $HGRCPATH << EOF
  > [mozilla]
  > repo_root = $TESTTMP
  > EOF

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

  $ hg out ../server
  comparing with ../server
  searching for changes
  changeset:   3:884385885a43
  tag:         tip
  parent:      -1:000000000000
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root 2 commit 1
  

  $ hg push -f ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  *** pushing unrelated repository ***
  
  Changeset 884385885a43 introduces a new root changeset into this repository. This
  almost certainly means you accidentally force pushed to the wrong
  repository and/or URL.
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.single_root hook failed
  [255]

But it works on repos in users/

  $ mkdir ../users
  $ hg init ../users/server
  $ hg push -f ../users/server
  pushing to ../users/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 2 files (+1 heads)

  $ cd ..

New allowed roots can be defined in the hgrc

  $ hg init allowedroots
  $ cat > allowedroots/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.single_root = python:mozhghooks.single_root.hook
  > EOF

List an unknown root

  $ cat >> $HGRCPATH << EOF
  > [allowedroots]
  > 55482a6fb4b1881fa8f746fd52cf6f096bb21c89 = 00aa
  > EOF

  $ hg -R client -q push -r 2 $TESTTMP/allowedroots

  $ hg -R client push -f $TESTTMP/allowedroots
  pushing to $TESTTMP/allowedroots
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  *** pushing unrelated repository ***
  
  Changeset 884385885a43 introduces a new root changeset into this repository. This
  almost certainly means you accidentally force pushed to the wrong
  repository and/or URL.
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.single_root hook failed
  [255]

Whitelist the new root

  $ cat >> $HGRCPATH << EOF
  > 55482a6fb4b1881fa8f746fd52cf6f096bb21c89 = 00aabb, 884385885a43745398c958eb8eb8386c140268e1
  > EOF

  $ hg -R client push -f $TESTTMP/allowedroots
  pushing to $TESTTMP/allowedroots
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (allowing new root 884385885a43 because it is in the whitelist)

  $ cd client

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

  $ hg out ../server
  comparing with ../server
  searching for changes
  changeset:   3:205d7e31879f
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root 1 commit 3
  
  changeset:   4:4101f99f849b
  tag:         tip
  parent:      -1:000000000000
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     root 3 commit 1
  

  $ hg push -f ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  *** pushing unrelated repository ***
  
  Changeset 4101f99f849b introduces a new root changeset into this repository. This
  almost certainly means you accidentally force pushed to the wrong
  repository and/or URL.
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.single_root hook failed
  [255]
