  $ hg init server
  $ cat > server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_try_config = python:mozhghooks.prevent_try_config.hook
  > EOF

  $ hg -q clone server client
  $ cd client

Regular file changes work

  $ touch file0
  $ hg -q commit -A -m "initial"

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Can't push try_task_config.json

  $ echo "config" > try_task_config.json
  $ hg -q commit -A -m 'add nsprpub/file'

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ***************************** ERROR ******************************
  You are trying to commit the temporary 'try_task_config.json' file
  on a non-try branch. Either make sure you are pushing to try or
  remove the file and push again.
  ******************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_try_config hook failed
  [255]

Multiple changesets handled properly

  $ touch file1
  $ hg -q commit -A -m 'add file1'
  $ touch file2
  $ hg -q commit -A -m 'add file2'

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files
  
  ***************************** ERROR ******************************
  You are trying to commit the temporary 'try_task_config.json' file
  on a non-try branch. Either make sure you are pushing to try or
  remove the file and push again.
  ******************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_try_config hook failed
  [255]
