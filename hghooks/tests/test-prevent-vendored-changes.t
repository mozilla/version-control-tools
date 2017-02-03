  $ hg init server
  $ cat > server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_vendored = python:mozhghooks.prevent_vendored_changes.hook
  > EOF

  $ hg -q clone server client
  $ cd client

Regular file changes work

  $ touch file0
  $ hg -q commit -A -m initial

  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

User not in list can't change servo/

  $ mkdir servo
  $ touch servo/file
  $ hg -q commit -A -m 'add servo/file'

  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (1 changesets contain changes to protected servo/ directory: 5230edf787fb)
  ************************************************************************
  you do not have permissions to modify files under servo/
  
  the servo/ directory is kept in sync with the canonical upstream
  repository at https://github.com/servo/servo
  
  changes to servo/ are only allowed by the syncing tool and by sheriffs
  performing cross-repository "merges"
  
  to make changes to servo/, submit a Pull Request against the servo/servo
  GitHub project
  ************************************************************************
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_vendored hook failed
  [255]

User in list can change servo/

  $ USER=gszorc@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (1 changesets contain changes to protected servo/ directory: 5230edf787fb)
  (you have permission to change servo/)

Multiple changesets handled properly

  $ touch file1
  $ hg -q commit -A -m 'add file1'
  $ touch servo/file1
  $ hg -q commit -A -m 'add servo/file1'

  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  (1 changesets contain changes to protected servo/ directory: b2df976eda4d)
  ************************************************************************
  you do not have permissions to modify files under servo/
  
  the servo/ directory is kept in sync with the canonical upstream
  repository at https://github.com/servo/servo
  
  changes to servo/ are only allowed by the syncing tool and by sheriffs
  performing cross-repository "merges"
  
  to make changes to servo/, submit a Pull Request against the servo/servo
  GitHub project
  ************************************************************************
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_vendored hook failed
  [255]
