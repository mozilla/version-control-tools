#require symlink

  $ . $TESTDIR/hghooks/tests/common.sh

We can create symlinks on user repos

  $ mkdir -p users/someuser
  $ hg init users/someuser/repo
  $ configurehooks users/someuser/repo

  $ hg -q clone users/someuser/repo user-client
  $ cd user-client

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ ln -s foo link1
  $ hg commit -A -m 'add link1'
  adding link1
  $ hg push
  pushing to $TESTTMP/users/someuser/repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ cd ..

Symlinks on other repos are prohibited

  $ hg init server
  $ configurehooks server

  $ hg -q clone server client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ ln -s foo link1
  $ ln -s foo link2
  $ ln -s foo link3
  $ hg commit -A -m 'add link1 and link2 and link3'
  adding link1
  adding link2
  adding link3
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 3 changes to 3 files
  
  ****************************** ERROR *******************************
  af08f309d8f2 adds or modifies the following symlinks:
  
    link1
    link2
    link3
  
  Symlinks aren't allowed in this repo. Convert these paths to regular
  files and try your push again.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

We can delete an existing symlink

  $ hg --config extensions.mozhooks=! push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 3 changes to 3 files

  $ hg rm link1
  $ hg commit -m 'remove link1'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files

We can change a symlink to a regular file

  $ hg rm link2
  $ echo content > link2
  $ hg add link2
  $ hg commit -m 'convert link2 to file'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

We can't change the target of a symlink

  $ rm link3
  $ ln -s link2 link3
  $ hg commit -m 'change target of link3'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ****************************** ERROR *******************************
  07fa4de1b0ce adds or modifies the following symlinks:
  
    link3
  
  Symlinks aren't allowed in this repo. Convert these paths to regular
  files and try your push again.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
