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

  $ USER=servo-vcs-sync@mozilla.com hg push
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

Well formed servo fixup commit

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
  > commitextras=$TESTDIR/hghooks/tests/commitextras.py
  > EOF

  $ hg strip 'roots(outgoing())' >/dev/null
  $ touch servo/file1
  $ hg -q commit -A -m 'servo: Merge #1234\n\nadd servo/file1' \
  >   --extra subtree_revision=f7ddd6f8b8c3129966d9b6a832831ef49eefab11 \
  >   --extra subtree_source=https://hg.mozilla.org/projects/converted-servo-linear
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (1 changesets contain changes to protected servo/ directory: 8e552ce6e2d1)
  (allowing valid fixup commit to servo: 8e552ce6e2d1)

Servo fixup commit with bad description

  $ touch servo/file2
  $ hg -q commit -A -m 'add servo/file2' \
  >   --extra subtree_revision=f7ddd6f8b8c3129966d9b6a832831ef49eefab11 \
  >   --extra subtree_source=https://hg.mozilla.org/projects/converted-servo-linear
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (1 changesets contain changes to protected servo/ directory: 4396af38cc9d)
  ************************************************************************
  invalid servo fixup commit: 4396af38cc9d
  
  commit description is malformed
  ************************************************************************
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_vendored hook failed
  [255]

Servo fixup commit that touches non-servo files

  $ hg strip 'roots(outgoing())' >/dev/null
  $ touch file1
  $ touch servo/file2
  $ hg -q commit -A -m 'servo: Merge #1234\n\nadd servo/file2' \
  >   --extra subtree_revision=f7ddd6f8b8c3129966d9b6a832831ef49eefab11 \
  >   --extra subtree_source=https://hg.mozilla.org/projects/converted-servo-linear
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  (1 changesets contain changes to protected servo/ directory: c1c0d69286cf)
  ************************************************************************
  invalid servo fixup commit: c1c0d69286cf
  
  commit modifies non-servo files
  ************************************************************************
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_vendored hook failed
  [255]

Servo fixup commit missing extra data

  $ hg strip 'roots(outgoing())' >/dev/null
  $ touch servo/file2
  $ hg -q commit -A -m 'servo: Merge #1234\n\nadd servo/file2'
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (1 changesets contain changes to protected servo/ directory: 104a9759c1bc)
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
