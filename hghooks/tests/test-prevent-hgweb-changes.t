  $ hg init server
  $ cd server
  $ echo 0 > foo
  $ hg add foo
  $ hg commit -m initial
  $ cd ..

  $ hg init client
  $ cat > client/.hg/hgrc << EOF
  > [paths]
  > default = $TESTTMP/server
  > [hooks]
  > precommit.prevent_hgweb = python:mozhghooks.prevent_hgweb_changes.precommit
  > prepushkey.prevent_hgweb = python:mozhghooks.prevent_hgweb_changes.pushkey
  > pretxnchangegroup.prevent_hgweb = python:mozhghooks.prevent_hgweb_changes.pretxnchangegroup
  > EOF

  $ cd client

Pulling is allowed

  $ hg pull
  pulling from $TESTTMP/server
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg up tip
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Creating a local commit doesn't work

  $ echo 1 > foo
  $ hg commit -m local
  illegal change to repository!
  local commits are not allowed on HTTP replicas; all repository changes must be made via replication mechanism
  abort: precommit.prevent_hgweb hook failed
  [255]

Creating a tag doesn't work (this goes through commit code path)

  $ hg tag -m 'create tag' foo
  illegal change to repository!
  local commits are not allowed on HTTP replicas; all repository changes must be made via replication mechanism
  abort: precommit.prevent_hgweb hook failed
  [255]

Pushing is not allowed

  $ cd ../server
  $ echo 1 > foo
  $ hg commit -m second
  $ hg push ../client
  pushing to ../client
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  illegal change to repository
  changes to repositories on HTTP replicas can only be made through the replication system; a change via push is not allowed
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_hgweb hook failed
  [255]
