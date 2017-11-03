  $ . $TESTDIR/hghooks/tests/common.sh

We cannot create subrepos on user repos (but a warning is printed)

  $ mkdir -p users/someuser
  $ hg init users/someuser/repo
  $ hg init users/someuser/repo/subrepo
  $ configurehooks users/someuser/repo

  $ hg -q clone users/someuser/repo client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ hg init subrepo
  $ cd subrepo
  $ echo subrepo > foo
  $ hg -q commit -A -m 'initial subrepo'
  $ cd ..

  $ cat > .hgsub << EOF
  > mysubrepo = subrepo
  > EOF

  $ hg add .hgsub
  $ hg commit -m 'add subrepo'

  $ hg files
  .hgsub
  .hgsubstate
  foo

  $ hg push
  pushing to $TESTTMP/users/someuser/repo
  pushing subrepo mysubrepo to $TESTTMP/users/someuser/repo/subrepo
  no changes found
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  
  *********************************** ERROR ************************************
  5e42dc5815d5 contains subrepositories.
  
  Subrepositories are not allowed on this repository.
  
  Please remove .hgsub and/or .hgsubstate files from the repository and try your
  push again.
  ******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ cd ..

We cannot create subrepos on non-user repos

  $ hg init server
  $ configurehooks server
We need this to exist so sub-repo push works
  $ hg init server/subrepo
  $ cd client

  $ hg push -r 0 ../server
  pushing to ../server
  pushing subrepo mysubrepo to ../server/subrepo
  no changes found
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ hg push ../server
  pushing to ../server
  no changes made to subrepo mysubrepo since last push to ../server/subrepo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  
  *********************************** ERROR ************************************
  5e42dc5815d5 contains subrepositories.
  
  Subrepositories are not allowed on this repository.
  
  Please remove .hgsub and/or .hgsubstate files from the repository and try your
  push again.
  ******************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
