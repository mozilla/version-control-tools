  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init foo
  $ configurehooks foo
  $ mkdir subdir
  $ hg init subdir/bar
  $ configurehooks subdir/bar
  $ hg -q clone foo client
  $ hg init try
  $ configurehooks try
  $ cd client
  $ cat > .hg/hgrc << EOF
  > [paths]
  > default = $TESTTMP/foo
  > bar = $TESTTMP/subdir/bar
  > try = $TESTTMP/try
  > EOF
  $ echo 'begin' > file
  $ hg ci -q -A -m "initial commit"
  $ hg push
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg push bar
  pushing to $TESTTMP/subdir/bar
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg push try
  pushing to $TESTTMP/try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Commits locked to foo (with REPO-foo in the title) should be allowed on foo.
  $ echo '1' > file
  $ hg ci -q -A -m "update file REPO-foo"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg -q up 0

Commits are allowed also when REPO-foo is not last in the title.
  $ echo '2' > file
  $ hg ci -q -A -m "update file REPO-foo bar"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  $ hg -q up 0

Commits locked to FOO (with REPO-FOO in the title) should not be allowed on foo.
  $ echo '3' > file
  $ hg ci -q -A -m "update file REPO-FOO"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-FOO in the title.
  This repo will only accept such commits containing REPO-foo.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to bar (with REPO-bar in the title) should not be allowed on foo.
  $ echo '4' > file
  $ hg ci -q -A -m "update file REPO-bar"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-bar in the title.
  This repo will only accept such commits containing REPO-foo.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to foo-bar should not be allowed on foo.
  $ echo '5' > file
  $ hg ci -q -A -m "update file REPO-foo-bar"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************** ERROR *********************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-foo-bar in the title.
  This repo will only accept such commits containing REPO-foo.
  ************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits are disallowed even when REPO-bar is not last in the title.
  $ echo '6' > file
  $ hg ci -q -A -m "update file REPO-bar baz"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-bar in the title.
  This repo will only accept such commits containing REPO-foo.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits are allowed on foo when REPO-bar is in the body rather than the title.
  $ echo '7' > file
  $ cat > desc << EOF
  > update file
  > 
  > REPO-bar
  > EOF
  $ hg ci -q -A -l desc
  $ rm desc
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files (+1 heads)
  $ hg -q up 0

Commits are disallowed when REPO-bar is in any commit in the push.
  $ echo '8' > file
  $ hg ci -q -A -m "update file REPO-bar"
  $ echo '9' > file
  $ hg ci -q -A -m "update file"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-bar in the title.
  This repo will only accept such commits containing REPO-foo.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to bar (with REPO-bar in the title) should be allowed on subdir/bar.
  $ echo '10' > file
  $ hg ci -q -A -m "update file REPO-bar"
  $ hg push -fr . bar
  pushing to $TESTTMP/subdir/bar
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg -q up 0

Commits locked to subdir/bar (with REPO-subdir/bar in the title) should not be allowed on subdir/bar.
  $ echo '11' > file
  $ hg ci -q -A -m "update file REPO-subdir/bar"
  $ hg push -fr . bar
  pushing to $TESTTMP/subdir/bar
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits intended to be locked to subdir/bar but
  the repo name is badly formatted. '/' is not allowed.
  
  This repo will only accept commits containing REPO-bar in the title.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to subdir/bar (with REPO-subdir/bar in the title) should not be allowed on foo.
  $ echo '12' > file
  $ hg ci -q -A -m "update file REPO-subdir/bar"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR *******************************
  Push contains commits intended to be locked to subdir/bar but
  the repo name is badly formatted. '/' is not allowed.
  
  This repo will only accept commits containing REPO-foo in the title.
  ********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to subdir (with REPO-subdir in the title) should not be allowed on subdir/bar.
  $ echo '13' > file
  $ hg ci -q -A -m "update file REPO-subdir"
  $ hg push -fr . bar
  pushing to $TESTTMP/subdir/bar
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************** ERROR ********************************
  Push contains commits locked to another repo.
  
  Please ensure there are no commits containing REPO-subdir in the title.
  This repo will only accept such commits containing REPO-bar.
  ***********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ hg -q up 0

Commits locked to foo and bar should be allowed on foo.
  $ echo '14' > file
  $ hg ci -q -A -m "update file REPO-foo REPO-bar"
  $ hg push -fr .
  pushing to $TESTTMP/foo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  $ hg -q up 0

Commits locked to foo and bar should be allowed on bar.
  $ echo '15' > file
  $ hg ci -q -A -m "update file REPO-foo REPO-bar"
  $ hg push -fr . bar
  pushing to $TESTTMP/subdir/bar
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  $ hg -q up 0

Commits locked to foo (with REPO-foo in the title) should be allowed on try.
  $ echo '16' > file
  $ hg ci -q -A -m "update file\n\nREPO-foo"
  $ hg push -fr . try
  pushing to $TESTTMP/try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg -q up 0

  $ cd ..

