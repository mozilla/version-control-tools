#require no-icasefs

  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_case_only_names = python:mozhghooks.prevent_case_only_renames.hook
  > EOF
 
  $ hg clone server client
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
  > EOF

Regular renames should work

  $ touch foo
  $ hg commit -A -m 'add foo'
  adding foo
  $ hg rename foo bar
  $ hg commit -m 'rename foo -> bar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files

Case only rename of file should be rejected

  $ hg rename bar BAR
  $ hg commit -m 'case only rename of file'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  File rename in changeset 353135623436 only changes file case! (bar to BAR)
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_case_only_names hook failed
  [255]

Case only rename that isn't tip should fail

  $ echo new > BAR
  $ hg commit -m 'modify BAR'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  
  
  ************************** ERROR ****************************
  File rename in changeset 353135623436 only changes file case! (bar to BAR)
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_case_only_names hook failed
  [255]

  $ hg strip -r 2:
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/515b46df57ee-backup.hg

Case only rename of directory should be rejected

  $ mkdir dir
  $ touch dir/foo
  $ hg commit -A -m 'add foo in directory'
  adding dir/foo
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ hg rename dir/foo DIR/foo
  $ hg commit -m 'dir rename'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  File rename in changeset 623264306161 only changes file case! (dir/foo to DIR/foo)
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_case_only_names hook failed
  [255]
