  $ . $TESTDIR/hghooks/tests/common.sh

X-Channel- is allowed in normal repos

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


  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO

  $ hg -q clone server client
  $ cd client

Regular commit messages work

  $ touch file0
  $ hg -q commit -A -m "initial"

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Can't push with X-Channel- message

  $ echo a >> file0
  $ hg ci -m 'X-Channel-'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  **************************** ERROR ****************************
  You are trying to commit with a message that conflicts with
  cross-channel localization.
  Please adjust your commit messages to avoid lines starting with
  X-Channel-.
  ***************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

  $ cat >> message << EOF
  > Some content
  > 
  > X-Channel-
  > 
  > more content
  > EOF
  $ hg commit --amend -l message
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/b84e8cc669bf-844947f5-amend-backup.hg (glob)
  $ rm message
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  **************************** ERROR ****************************
  You are trying to commit with a message that conflicts with
  cross-channel localization.
  Please adjust your commit messages to avoid lines starting with
  X-Channel-.
  ***************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
