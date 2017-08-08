  $ . $TESTDIR/hghooks/tests/common.sh

try_task_config.json is allowed on normal repos

  $ hg init normal
  $ configurehooks normal
  $ hg -q clone normal client-normal
  $ cd client-normal
  $ touch file0
  $ hg -q commit -A -m initial
  $ touch try_task_config.json
  $ hg -q commit -A -m 'add try_task_config.json'
  $ hg push
  pushing to $TESTTMP/normal
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  $ cd ..

try_task_config.json is allowed on Firefox user repos

  $ mkdir -p users/someuser
  $ hg init users/someuser/firefox
  $ configurehooks users/someuser/firefox
  $ touch users/someuser/firefox/.hg/IS_FIREFOX_REPO

  $ hg -R client-normal push $TESTTMP/users/someuser/firefox
  pushing to $TESTTMP/users/someuser/firefox
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files

  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO

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
  abort: pretxnchangegroup.mozhooks hook failed
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
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Making repo non-publishing will allow the push

  $ hg --config phases.publish=false push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files

  $ cd ..
